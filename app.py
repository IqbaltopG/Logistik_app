from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rahasia-logistik-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/logistik_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELS ---
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)
    role = db.Column(db.Enum('admin', 'customer'), nullable=False)
    orders = db.relationship('Order', backref='user', lazy=True)

class Tarif(db.Model):
    __tablename__ = 'tarif'
    id = db.Column(db.Integer, primary_key=True)
    kota_asal = db.Column(db.String(100), nullable=False)
    kota_tujuan = db.Column(db.String(100), nullable=False)
    harga = db.Column(db.Integer, nullable=False)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    detail_barang = db.Column(db.Text, nullable=False)
    kota_asal = db.Column(db.String(100), nullable=False)
    kota_tujuan = db.Column(db.String(100), nullable=False)
    status_order = db.Column(db.Enum('Pending', 'Valid', 'Tidak Valid'), default='Pending')
    
    pengiriman = db.relationship('Pengiriman', backref='order', uselist=False, cascade='all, delete-orphan')

class Pengiriman(db.Model):
    __tablename__ = 'pengiriman'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    driver_nama = db.Column(db.String(255), nullable=False)
    armada_plat = db.Column(db.String(50), nullable=False)
    status_pengiriman = db.Column(db.Enum('Penjadwalan', 'Di Perjalanan', 'Terkirim'), default='Penjadwalan')
    epod_ref = db.Column(db.String(255), nullable=True)

# --- DECORATORS ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        else:
            flash('Username atau password salah', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    if session['role'] == 'admin':
        total_orders = Order.query.count()
        pending_orders = Order.query.filter_by(status_order='Pending').count()
        valid_orders = Order.query.filter_by(status_order='Valid').count()
        pengiriman_berjalan = Pengiriman.query.filter_by(status_pengiriman='Di Perjalanan').count()
        pengiriman_selesai = Pengiriman.query.filter_by(status_pengiriman='Terkirim').count()
    else:
        total_orders = Order.query.filter_by(user_id=session['user_id']).count()
        pending_orders = Order.query.filter_by(user_id=session['user_id'], status_order='Pending').count()
        valid_orders = Order.query.filter_by(user_id=session['user_id'], status_order='Valid').count()
        pengiriman_berjalan = db.session.query(Pengiriman).join(Order).filter(Order.user_id == session['user_id'], Pengiriman.status_pengiriman == 'Di Perjalanan').count()
        pengiriman_selesai = db.session.query(Pengiriman).join(Order).filter(Order.user_id == session['user_id'], Pengiriman.status_pengiriman == 'Terkirim').count()
    
    return render_template('dashboard.html', 
                           total_orders=total_orders,
                           pending_orders=pending_orders,
                           valid_orders=valid_orders,
                           pengiriman_berjalan=pengiriman_berjalan,
                           pengiriman_selesai=pengiriman_selesai)

@app.route('/cek_harga', methods=['GET', 'POST'])
@login_required
def cek_harga():
    hasil = None
    if request.method == 'POST':
        asal = request.form.get('kota_asal')
        tujuan = request.form.get('kota_tujuan')
        hasil = Tarif.query.filter_by(kota_asal=asal, kota_tujuan=tujuan).first()
        if not hasil:
            flash('Tarif tidak ditemukan untuk rute tersebut.', 'error')
            
    kotas = db.session.query(Tarif.kota_asal).distinct().all()
    tujuans = db.session.query(Tarif.kota_tujuan).distinct().all()
    return render_template('cek_harga.html', hasil=hasil, kotas=[k[0] for k in kotas], tujuans=[t[0] for t in tujuans])

@app.route('/orders', methods=['GET', 'POST'])
@login_required
def orders():
    if request.method == 'POST' and session['role'] == 'customer':
        asal = request.form.get('kota_asal')
        tujuan = request.form.get('kota_tujuan')
        detail = request.form.get('detail_barang')
        new_order = Order(user_id=session['user_id'], kota_asal=asal, kota_tujuan=tujuan, detail_barang=detail)
        db.session.add(new_order)
        db.session.commit()
        return redirect(url_for('orders'))
    
    if session['role'] == 'admin':
        all_orders = Order.query.all()
    else:
        all_orders = Order.query.filter_by(user_id=session['user_id']).all()
        
    return render_template('orders.html', orders=all_orders)

@app.route('/orders/validate/<int:id>', methods=['POST'])
@login_required
@admin_required
def validate_order(id):
    order = Order.query.get_or_404(id)
    status = request.form.get('status_order')
    if status in ['Valid', 'Tidak Valid']:
        order.status_order = status
        db.session.commit()
    return redirect(url_for('orders'))

@app.route('/pengiriman', methods=['GET', 'POST'])
@login_required
def pengiriman():
    if request.method == 'POST' and session['role'] == 'admin':
        order_id = request.form.get('order_id')
        driver = request.form.get('driver_nama')
        armada = request.form.get('armada_plat')
        new_pengiriman = Pengiriman(order_id=order_id, driver_nama=driver, armada_plat=armada)
        db.session.add(new_pengiriman)
        db.session.commit()
        return redirect(url_for('pengiriman'))
    
    if session['role'] == 'admin':
        orders_ready = Order.query.filter_by(status_order='Valid').filter(~Order.pengiriman.has()).all()
        all_pengiriman = Pengiriman.query.all()
    else:
        orders_ready = []
        all_pengiriman = db.session.query(Pengiriman).join(Order).filter(Order.user_id == session['user_id']).all()
        
    return render_template('pengiriman.html', orders_ready=orders_ready, pengiriman=all_pengiriman)

@app.route('/pengiriman/update/<int:id>', methods=['POST'])
@login_required
@admin_required
def update_pengiriman(id):
    p = Pengiriman.query.get_or_404(id)
    status = request.form.get('status_pengiriman')
    epod = request.form.get('epod_ref')
    
    if status in ['Penjadwalan', 'Di Perjalanan', 'Terkirim']:
        p.status_pengiriman = status
        if status == 'Terkirim':
            p.epod_ref = epod
        else:
            p.epod_ref = None
        db.session.commit()
    return redirect(url_for('pengiriman'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
