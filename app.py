from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rahasia-logistik-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/logistik_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

def format_rupiah(value):
    """Format number to Indonesian Rupiah currency format."""
    if value is None:
        return "Rp 0"
    return f"Rp {int(value):,}".replace(',', '.')

app.jinja_env.filters['rupiah'] = format_rupiah

db = SQLAlchemy(app)

# --- MODELS ---
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('admin', 'customer'), nullable=False)
    orders = db.relationship('Order', backref='user', lazy=True)

class Tarif(db.Model):
    __tablename__ = 'tarif'
    id = db.Column(db.Integer, primary_key=True)
    kota_asal = db.Column(db.String(100), nullable=False)
    kota_tujuan = db.Column(db.String(100), nullable=False)
    harga_dasar = db.Column(db.Float, nullable=False)
    harga_per_kg = db.Column(db.Float, nullable=False)
    harga_per_m3 = db.Column(db.Float, nullable=False)

class Armada(db.Model):
    __tablename__ = 'armada'
    id = db.Column(db.Integer, primary_key=True)
    plat_nomor = db.Column(db.String(50), nullable=False, unique=True)
    tipe_armada = db.Column(db.Enum('Tronton', 'Trailer', 'Dolly'), nullable=False)
    status = db.Column(db.Enum('Tersedia', 'Beroperasi'), default='Tersedia')

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    detail_barang = db.Column(db.Text, nullable=False)
    tipe_barang = db.Column(db.Enum('Container', 'Cargo'), nullable=False)
    kota_asal = db.Column(db.String(100), nullable=False)
    kota_tujuan = db.Column(db.String(100), nullable=False)
    berat_kg = db.Column(db.Float, nullable=False)
    dimensi_p = db.Column(db.Float, nullable=True)
    dimensi_l = db.Column(db.Float, nullable=True)
    dimensi_t = db.Column(db.Float, nullable=True)
    estimasi_harga = db.Column(db.Float, nullable=False)
    status_order = db.Column(db.Enum('Pending', 'Valid', 'Tidak Valid'), default='Pending')
    
    pengiriman = db.relationship('Pengiriman', backref='order', uselist=False, cascade='all, delete-orphan')

class Pengiriman(db.Model):
    __tablename__ = 'pengiriman'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    driver_nama = db.Column(db.String(255), nullable=False)
    armada_id = db.Column(db.Integer, db.ForeignKey('armada.id'), nullable=False)
    status_pengiriman = db.Column(db.Enum('Penjadwalan', 'Di Perjalanan', 'Terkirim'), default='Penjadwalan')
    epod_ref = db.Column(db.String(255), nullable=True)
    
    armada = db.relationship('Armada', backref='pengiriman', lazy=True)

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
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        else:
            flash('Username atau password salah', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Password dan Konfirmasi Password tidak cocok!', 'error')
            return redirect(url_for('register'))
            
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username sudah terdaftar. Silakan gunakan username lain.', 'error')
        else:
            hashed_pw = generate_password_hash(password)
            new_user = User(username=username, password=hashed_pw, role='customer')
            db.session.add(new_user)
            db.session.commit()
            flash('Registrasi berhasil! Silakan login menggunakan akun Anda.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

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
    kalkulasi = None
    if request.method == 'POST':
        asal = request.form.get('kota_asal')
        tujuan = request.form.get('kota_tujuan')
        berat = float(request.form.get('berat_kg') or 0)
        p = float(request.form.get('dimensi_p') or 0)
        l = float(request.form.get('dimensi_l') or 0)
        t = float(request.form.get('dimensi_t') or 0)
        hasil = Tarif.query.filter_by(kota_asal=asal, kota_tujuan=tujuan).first()
        if not hasil:
            flash('Tarif tidak ditemukan untuk rute tersebut.', 'error')
        else:
            volume = p * l * t
            estimasi = hasil.harga_dasar + (berat * hasil.harga_per_kg) + (volume * hasil.harga_per_m3)
            kalkulasi = {'berat': berat, 'volume': volume, 'estimasi': estimasi}
            
    kotas = db.session.query(Tarif.kota_asal).distinct().all()
    tujuans = db.session.query(Tarif.kota_tujuan).distinct().all()
    return render_template('cek_harga.html', hasil=hasil, kalkulasi=kalkulasi, kotas=[k[0] for k in kotas], tujuans=[t[0] for t in tujuans])

@app.route('/orders', methods=['GET', 'POST'])
@login_required
def orders():
    if request.method == 'POST' and session['role'] == 'customer':
        asal = request.form.get('kota_asal')
        tujuan = request.form.get('kota_tujuan')
        detail = request.form.get('detail_barang')
        tipe = request.form.get('tipe_barang')
        berat = float(request.form.get('berat_kg') or 0)

        p_str = request.form.get('dimensi_p')
        l_str = request.form.get('dimensi_l')
        t_str = request.form.get('dimensi_t')

        p = float(p_str) if p_str else None
        l = float(l_str) if l_str else None
        t = float(t_str) if t_str else None
        
        tarif = Tarif.query.filter_by(kota_asal=asal, kota_tujuan=tujuan).first()
        estimasi_harga = 0
        if tarif:
            p_calc = p or 0.0
            l_calc = l or 0.0
            t_calc = t or 0.0
            volume = p_calc * l_calc * t_calc
            estimasi_harga = tarif.harga_dasar + (berat * tarif.harga_per_kg) + (volume * tarif.harga_per_m3)
            
        new_order = Order(user_id=session['user_id'], kota_asal=asal, kota_tujuan=tujuan, 
                          detail_barang=detail, tipe_barang=tipe, berat_kg=berat,
                          dimensi_p=p, dimensi_l=l, dimensi_t=t, estimasi_harga=estimasi_harga)
        db.session.add(new_order)
        db.session.commit()
        return redirect(url_for('orders'))
    
    if session['role'] == 'admin':
        all_orders = Order.query.all()
    else:
        all_orders = Order.query.filter_by(user_id=session['user_id']).all()
        
    kotas = db.session.query(Tarif.kota_asal).distinct().all()
    tujuans = db.session.query(Tarif.kota_tujuan).distinct().all()
    return render_template('orders.html', orders=all_orders, kotas=[k[0] for k in kotas], tujuans=[t[0] for t in tujuans])

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

@app.route('/armada', methods=['GET', 'POST'])
@login_required
@admin_required
def armada():
    edit_id = request.args.get('edit_id', type=int)
    armada_to_edit = None
    if edit_id:
        armada_to_edit = Armada.query.get(edit_id)

    all_armadas = Armada.query.order_by(Armada.id).all()
    return render_template('armada.html', armadas=all_armadas, armada_to_edit=armada_to_edit)

@app.route('/armada/add', methods=['POST'])
@login_required
@admin_required
def add_armada():
    plat = request.form.get('plat_nomor')
    tipe = request.form.get('tipe_armada')
    status = request.form.get('status')
    new_armada = Armada(plat_nomor=plat, tipe_armada=tipe, status=status)
    db.session.add(new_armada)
    db.session.commit()
    flash('Armada baru berhasil ditambahkan.', 'success')
    return redirect(url_for('armada'))

@app.route('/armada/edit/<int:id>', methods=['POST'])
@login_required
@admin_required
def edit_armada(id):
    armada_to_edit = Armada.query.get_or_404(id)
    armada_to_edit.plat_nomor = request.form.get('plat_nomor')
    armada_to_edit.tipe_armada = request.form.get('tipe_armada')
    armada_to_edit.status = request.form.get('status')
    db.session.commit()
    flash(f'Armada ID {id} berhasil diperbarui.', 'success')
    return redirect(url_for('armada'))

@app.route('/armada/delete/<int:id>')
@login_required
@admin_required
def delete_armada(id):
    armada_to_delete = Armada.query.get_or_404(id)
    if armada_to_delete.status == 'Beroperasi':
        flash(f'Armada {armada_to_delete.plat_nomor} sedang beroperasi dan tidak bisa dihapus.', 'error')
        return redirect(url_for('armada'))
    db.session.delete(armada_to_delete)
    db.session.commit()
    flash(f'Armada {armada_to_delete.plat_nomor} berhasil dihapus.', 'success')
    return redirect(url_for('armada'))

@app.route('/pengiriman', methods=['GET', 'POST'])
@login_required
def pengiriman():
    if request.method == 'POST' and session['role'] == 'admin':
        order_id = request.form.get('order_id')
        driver = request.form.get('driver_nama')
        armada_id = request.form.get('armada_id')
        new_pengiriman = Pengiriman(order_id=order_id, driver_nama=driver, armada_id=armada_id)
        db.session.add(new_pengiriman)
        
        armada_dipilih = Armada.query.get(armada_id)
        if armada_dipilih:
            armada_dipilih.status = 'Beroperasi'
            
        db.session.commit()
        return redirect(url_for('pengiriman'))
    
    if session['role'] == 'admin':
        orders_ready = Order.query.filter_by(status_order='Valid').filter(~Order.pengiriman.has()).all()
        all_pengiriman = Pengiriman.query.all()
        armada_tersedia = Armada.query.filter_by(status='Tersedia').all()
    else:
        orders_ready = []
        all_pengiriman = db.session.query(Pengiriman).join(Order).filter(Order.user_id == session['user_id']).all()
        armada_tersedia = []
        
    return render_template('pengiriman.html', orders_ready=orders_ready, pengiriman=all_pengiriman, armada_tersedia=armada_tersedia)

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
            if p.armada:
                p.armada.status = 'Tersedia'
        else:
            p.epod_ref = None
        db.session.commit()
    return redirect(url_for('pengiriman'))

@app.route('/tarif')
@login_required
@admin_required
def tarif():
    edit_id = request.args.get('edit_id', type=int)
    tarif_to_edit = None
    if edit_id:
        tarif_to_edit = Tarif.query.get(edit_id)

    all_tarifs = Tarif.query.order_by(Tarif.id).all()
    return render_template('tarif.html', tarifs=all_tarifs, tarif_to_edit=tarif_to_edit)

@app.route('/tarif/add', methods=['POST'])
@login_required
@admin_required
def add_tarif():
    new_tarif = Tarif(
        kota_asal=request.form.get('kota_asal'),
        kota_tujuan=request.form.get('kota_tujuan'),
        harga_dasar=float(request.form.get('harga_dasar')),
        harga_per_kg=float(request.form.get('harga_per_kg')),
        harga_per_m3=float(request.form.get('harga_per_m3'))
    )
    db.session.add(new_tarif)
    db.session.commit()
    flash('Rute & tarif baru berhasil ditambahkan.', 'success')
    return redirect(url_for('tarif'))

@app.route('/tarif/edit/<int:id>', methods=['POST'])
@login_required
@admin_required
def edit_tarif(id):
    tarif_to_edit = Tarif.query.get_or_404(id)
    tarif_to_edit.kota_asal = request.form.get('kota_asal')
    tarif_to_edit.kota_tujuan = request.form.get('kota_tujuan')
    tarif_to_edit.harga_dasar = float(request.form.get('harga_dasar'))
    tarif_to_edit.harga_per_kg = float(request.form.get('harga_per_kg'))
    tarif_to_edit.harga_per_m3 = float(request.form.get('harga_per_m3'))
    db.session.commit()
    flash(f'Tarif ID {id} berhasil diperbarui.', 'success')
    return redirect(url_for('tarif'))

@app.route('/tarif/delete/<int:id>')
@login_required
@admin_required
def delete_tarif(id):
    tarif_to_delete = Tarif.query.get_or_404(id)
    db.session.delete(tarif_to_delete)
    db.session.commit()
    flash(f'Tarif ID {id} berhasil dihapus.', 'success')
    return redirect(url_for('tarif'))

@app.cli.command("seed")
def seed_command():
    """Mengisi database dengan data dummy."""
    from seed import seed_database
    seed_database()
    print("Database seeding completed!")


def init_dummy_users():
    with app.app_context():
        db.create_all()
        if User.query.first() is None:
            admin = User(username='admin', password=generate_password_hash('admin'), role='admin')
            cust1 = User(username='cust1', password=generate_password_hash('cust1'), role='customer')
            db.session.add_all([admin, cust1])
            db.session.commit()

if __name__ == '__main__':
    init_dummy_users()
    app.run(host='0.0.0.0', port=5000, debug=True)
