from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, Category, Transaction, User
from datetime import datetime, date
import calendar

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # 未ログイン時に飛ばす先
login_manager.login_message = 'ログインが必要です'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ===== 認証まわり =====

@app.route('/signup', methods=['GET'])
def signup_form():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup():
    email = request.form['email']
    password = request.form['password']
    name = request.form.get('name', '')

    existing = User.query.filter_by(email=email).first()
    if existing:
        flash('このメールアドレスは既に登録されています')
        return redirect(url_for('signup_form'))

    new_user = User(email=email, name=name)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    login_user(new_user)
    return redirect(url_for('index'))

@app.route('/login', methods=['GET'])
def login_form():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        flash('メールアドレスまたはパスワードが違います')
        return redirect(url_for('login_form'))

    login_user(user)
    return redirect(url_for('index'))

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login_form'))


# ===== ここから下の全ルートに @login_required を追加 =====

@app.route('/')
@login_required
def index():
    categories = Category.query.filter((Category.user_id == None) | (Category.user_id == current_user.id)).all()
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.transaction_date.desc()).all()
    return render_template('dashboard.html', categories=categories, transactions=transactions)

@app.route('/transactions/new', methods=['GET'])
@login_required
def new_transaction_form():
    categories = Category.query.filter((Category.user_id == None) | (Category.user_id == current_user.id)).all()
    return render_template('transaction_form.html', categories=categories)

@app.route('/transactions/new', methods=['POST'])
@login_required
def create_transaction():
    new_transaction = Transaction(
        user_id=current_user.id,
        category_id=request.form['category_id'],
        amount=request.form['amount'],
        type=request.form['type'],
        memo=request.form.get('memo', ''),
        transaction_date=datetime.strptime(request.form['transaction_date'], '%Y-%m-%d').date()
    )
    db.session.add(new_transaction)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/transactions/<int:id>/edit', methods=['GET'])
@login_required
def edit_transaction_form(id):
    transaction = Transaction.query.get_or_404(id)
    if transaction.user_id != current_user.id:
        return redirect(url_for('index'))
    categories = Category.query.filter((Category.user_id == None) | (Category.user_id == current_user.id)).all()
    return render_template('transaction_form.html', categories=categories, transaction=transaction)

@app.route('/transactions/<int:id>/edit', methods=['POST'])
@login_required
def update_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    if transaction.user_id != current_user.id:
        return redirect(url_for('index'))
    transaction.category_id = request.form['category_id']
    transaction.amount = request.form['amount']
    transaction.type = request.form['type']
    transaction.memo = request.form.get('memo', '')
    transaction.transaction_date = datetime.strptime(request.form['transaction_date'], '%Y-%m-%d').date()
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/transactions/<int:id>/delete', methods=['POST'])
@login_required
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    if transaction.user_id != current_user.id:
        return redirect(url_for('index'))
    db.session.delete(transaction)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/calendar')
@login_required
def calendar_view():
    year = request.args.get('year', type=int, default=date.today().year)
    month = request.args.get('month', type=int, default=date.today().month)

    first_day = date(year, month, 1)
    last_day_num = calendar.monthrange(year, month)[1]
    last_day = date(year, month, last_day_num)

    transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_date >= first_day,
        Transaction.transaction_date <= last_day
    ).all()

    daily_summary = {}
    for t in transactions:
        day = t.transaction_date.day
        if day not in daily_summary:
            daily_summary[day] = {'expense': 0, 'income': 0}
        daily_summary[day][t.type] += float(t.amount)

    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdayscalendar(year, month)

    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)

    month_total_expense = sum(v['expense'] for v in daily_summary.values())
    month_total_income = sum(v['income'] for v in daily_summary.values())

    return render_template(
        'calendar.html',
        year=year, month=month, weeks=weeks,
        daily_summary=daily_summary,
        prev_year=prev_year, prev_month=prev_month,
        next_year=next_year, next_month=next_month,
        today=date.today(),
        month_total_expense=month_total_expense,
        month_total_income=month_total_income
    )

@app.route('/calendar/day/<date_str>')
@login_required
def day_detail(date_str):
    selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    transactions = Transaction.query.filter_by(
        user_id=current_user.id,
        transaction_date=selected_date
    ).order_by(Transaction.created_at).all()
    return render_template('day_detail.html', selected_date=selected_date, transactions=transactions)

@app.route('/summary')
@login_required
def summary_view():
    year = request.args.get('year', type=int, default=date.today().year)
    month = request.args.get('month', type=int, default=date.today().month)

    first_day = date(year, month, 1)
    last_day_num = calendar.monthrange(year, month)[1]
    last_day = date(year, month, last_day_num)

    transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_date >= first_day,
        Transaction.transaction_date <= last_day
    ).all()

    total_expense = sum(float(t.amount) for t in transactions if t.type == 'expense')
    total_income = sum(float(t.amount) for t in transactions if t.type == 'income')
    balance = total_income - total_expense

    # カテゴリごとに集計
    category_totals = {}
    for t in transactions:
        cat = t.category
        if cat.id not in category_totals:
            category_totals[cat.id] = {
                'name': cat.name, 'color': cat.color, 'type': cat.type, 'amount': 0
            }
        category_totals[cat.id]['amount'] += float(t.amount)

    expense_breakdown = sorted(
        [v for v in category_totals.values() if v['type'] == 'expense'],
        key=lambda x: x['amount'], reverse=True
    )
    income_breakdown = sorted(
        [v for v in category_totals.values() if v['type'] == 'income'],
        key=lambda x: x['amount'], reverse=True
    )

    # 割合(%)を計算(バーの幅に使う)
    for item in expense_breakdown:
        item['percent'] = round(item['amount'] / total_expense * 100) if total_expense > 0 else 0
    for item in income_breakdown:
        item['percent'] = round(item['amount'] / total_income * 100) if total_income > 0 else 0

    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)

    return render_template(
        'summary.html',
        year=year, month=month,
        total_expense=total_expense, total_income=total_income, balance=balance,
        expense_breakdown=expense_breakdown, income_breakdown=income_breakdown,
        prev_year=prev_year, prev_month=prev_month,
        next_year=next_year, next_month=next_month
    )

@app.route('/categories/new', methods=['GET'])
@login_required
def new_category_form():
    return render_template('category_form.html')

@app.route('/categories/new', methods=['POST'])
@login_required
def create_category():
    name = request.form['name'].strip()
    cat_type = request.form['type']
    color = request.form['color']

    if not name:
        flash('カテゴリ名を入力してください')
        return redirect(url_for('new_category_form'))

    new_category = Category(
        user_id=current_user.id,
        name=name,
        type=cat_type,
        color=color
    )
    db.session.add(new_category)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)