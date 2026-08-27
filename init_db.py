from app import app
from models import db, Category, User

default_categories = [
    # 支出カテゴリ
    {'name': '食費', 'type': 'expense', 'color': '#FF6B6B'},
    {'name': '交通費', 'type': 'expense', 'color': '#4ECDC4'},
    {'name': '娯楽費', 'type': 'expense', 'color': '#FFD93D'},
    {'name': '日用品', 'type': 'expense', 'color': '#95E1D3'},
    {'name': '住居費', 'type': 'expense', 'color': '#A8E6CF'},
    {'name': '光熱費', 'type': 'expense', 'color': '#FFA07A'},
    {'name': 'その他(支出)', 'type': 'expense', 'color': '#C9C9C9'},
    # 収入カテゴリ
    {'name': '給与', 'type': 'income', 'color': '#6BCB77'},
    {'name': 'お小遣い', 'type': 'income', 'color': '#4D96FF'},
    {'name': 'その他(収入)', 'type': 'income', 'color': '#B4A7D6'},
]

with app.app_context():
    # デフォルトカテゴリの登録
    for cat in default_categories:
        existing = Category.query.filter_by(name=cat['name'], user_id=None).first()
        if not existing:
            new_category = Category(
                name=cat['name'],
                type=cat['type'],
                color=cat['color'],
                user_id=None
            )
            db.session.add(new_category)

    db.session.commit()
    print('デフォルトカテゴリを登録しました')

    # 仮ユーザーの作成
    existing_user = User.query.filter_by(email='test@example.com').first()
    if not existing_user:
        temp_user = User(email='test@example.com', name='テストユーザー')
        temp_user.set_password('password123')
        db.session.add(temp_user)
        db.session.commit()
        print('仮ユーザーを作成しました(email: test@example.com / password: password123)')