from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///evolution.db'
db = SQLAlchemy(app)

# 元素模型
class Element(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(200))
    category = db.Column(db.String(50))  # 基础元素、物质、生命等
    discovered = db.Column(db.Boolean, default=False)
    icon = db.Column(db.String(50))  # 元素图标类名

# 组合规则模型
class Combination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    element1_id = db.Column(db.Integer, db.ForeignKey('element.id'))
    element2_id = db.Column(db.Integer, db.ForeignKey('element.id'))
    result_id = db.Column(db.Integer, db.ForeignKey('element.id'))
    description = db.Column(db.String(200))  # 组合过程的描述

# 初始化基础元素
def init_basic_elements():
    basic_elements = [
        {
            'name': '能量',
            'description': '宇宙中最基本的形式',
            'category': '基础',
            'icon': 'fas fa-bolt'
        },
        {
            'name': '物质',
            'description': '能量凝聚的结果',
            'category': '基础',
            'icon': 'fas fa-atom'
        },
        {
            'name': '时间',
            'description': '宇宙的第四维度',
            'category': '基础',
            'icon': 'fas fa-clock'
        },
        {
            'name': '空间',
            'description': '宇宙的三维结构',
            'category': '基础',
            'icon': 'fas fa-cube'
        }
    ]
    
    for elem in basic_elements:
        if not Element.query.filter_by(name=elem['name']).first():
            element = Element(
                name=elem['name'],
                description=elem['description'],
                category=elem['category'],
                icon=elem['icon'],
                discovered=True
            )
            db.session.add(element)
    
    db.session.commit()

# 初始化组合规则
def init_combinations():
    # 示例组合规则
    combinations = [
        {
            'element1': '能量',
            'element2': '空间',
            'result': '宇宙',
            'description': '能量在空间中扩展，形成了宇宙'
        },
        {
            'element1': '能量',
            'element2': '物质',
            'result': '原子',
            'description': '能量与物质的相互作用形成了原子'
        }
    ]
    
    for combo in combinations:
        elem1 = Element.query.filter_by(name=combo['element1']).first()
        elem2 = Element.query.filter_by(name=combo['element2']).first()
        result = Element.query.filter_by(name=combo['result']).first()
        
        if not result:
            result = Element(
                name=combo['result'],
                description=combo['description'],
                category='复合',
                discovered=False,
                icon='fas fa-question'
            )
            db.session.add(result)
            db.session.commit()
        
        if not Combination.query.filter_by(
            element1_id=elem1.id,
            element2_id=elem2.id
        ).first():
            combination = Combination(
                element1_id=elem1.id,
                element2_id=elem2.id,
                result_id=result.id,
                description=combo['description']
            )
            db.session.add(combination)
    
    db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/elements')
def get_elements():
    elements = Element.query.filter_by(discovered=True).all()
    return jsonify([{
        'id': e.id,
        'name': e.name,
        'description': e.description,
        'category': e.category,
        'icon': e.icon
    } for e in elements])

@app.route('/api/combine', methods=['POST'])
def combine_elements():
    data = request.get_json()
    elem1_id = data.get('element1_id')
    elem2_id = data.get('element2_id')
    
    combination = Combination.query.filter(
        ((Combination.element1_id == elem1_id) & (Combination.element2_id == elem2_id)) |
        ((Combination.element1_id == elem2_id) & (Combination.element2_id == elem1_id))
    ).first()
    
    if combination:
        result = Element.query.get(combination.result_id)
        result.discovered = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'result': {
                'id': result.id,
                'name': result.name,
                'description': result.description,
                'category': result.category,
                'icon': result.icon
            },
            'description': combination.description
        })
    
    return jsonify({
        'success': False,
        'message': '这个组合没有产生新的发现'
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_basic_elements()
        init_combinations()
    app.run(debug=True) 