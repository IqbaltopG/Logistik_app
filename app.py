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
    rute = db.Column(db.String(255), nullable=False)
    harga_cdd = db.Column(db.Integer, nullable=False)
    harga_fuso = db.Column(db.Integer, nullable=False)
    harga_tronton = db.Column(db.Integer, nullable=False)
    harga_trailer = db.Column(db.Integer, nullable=False)

class Armada(db.Model):
    __tablename__ = 'armada'
    id = db.Column(db.Integer, primary_key=True)
    plat_nomor = db.Column(db.String(50), nullable=False, unique=True)
    tipe_armada = db.Column(db.Enum('CDD', 'Fuso', 'Tronton', 'Trailer', 'Trailer 20 Feet', 'Trailer 40 Feet', 'Dolly'), nullable=False)
    status = db.Column(db.Enum('Tersedia', 'Beroperasi'), default='Tersedia')

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    detail_barang = db.Column(db.Text, nullable=False)
    jenis_layanan = db.Column(db.String(50), nullable=False)
    rute = db.Column(db.String(255), nullable=False)
    jenis_armada = db.Column(db.String(50), nullable=False)
    jumlah_unit = db.Column(db.Integer, default=1)
    total_harga = db.Column(db.Integer, nullable=False)
    status_order = db.Column(db.Enum('Pending', 'Valid', 'Tidak Valid'), default='Pending')
    status_pembayaran = db.Column(db.String(50), default='Belum Bayar')
    no_resi = db.Column(db.String(100), nullable=True, unique=True)
    alasan_pembatalan = db.Column(db.Text, nullable=True)
    cancelled_by = db.Column(db.Enum('Customer', 'Admin'), nullable=True)
    
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
            
        # Verifikasi user masih ada di database
        user = User.query.get(session['user_id'])
        if not user:
            session.clear()
            flash('Sesi tidak valid, silakan login kembali.', 'error')
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
        rute = request.form.get('rute')
        jenis_armada = request.form.get('jenis_armada')
        jumlah_unit = int(request.form.get('jumlah_unit') or 1)
        
        hasil = Tarif.query.filter_by(rute=rute).first()
        if not hasil:
            flash('Tarif tidak ditemukan untuk rute tersebut.', 'error')
        else:
            harga_satuan = 0
            if jenis_armada == 'CDD':
                harga_satuan = hasil.harga_cdd
            elif jenis_armada == 'Fuso':
                harga_satuan = hasil.harga_fuso
            elif jenis_armada == 'Tronton':
                harga_satuan = hasil.harga_tronton
            elif jenis_armada in ['Trailer 20 Feet', 'Trailer 40 Feet']:
                harga_satuan = hasil.harga_trailer
                
            kalkulasi = {
                'rute': rute,
                'jenis_armada': jenis_armada,
                'jumlah_unit': jumlah_unit,
                'harga_satuan': harga_satuan,
                'total_harga': harga_satuan * jumlah_unit
            }
            
    rutes = db.session.query(Tarif.rute).distinct().all()
    return render_template('cek_harga.html', hasil=hasil, kalkulasi=kalkulasi, rutes=[r[0] for r in rutes])

@app.route('/orders', methods=['GET', 'POST'])
@login_required
def orders():
    if request.method == 'POST' and session['role'] == 'customer':
        rute = request.form.get('rute')
        detail = request.form.get('detail_barang')
        jenis_layanan = request.form.get('jenis_layanan')
        jenis_armada = request.form.get('jenis_armada')
        jumlah_unit = int(request.form.get('jumlah_unit') or 1)
        
        tarif = Tarif.query.filter_by(rute=rute).first()
        total_harga = 0
        if tarif:
            harga_satuan = 0
            if jenis_armada == 'CDD':
                harga_satuan = tarif.harga_cdd
            elif jenis_armada == 'Fuso':
                harga_satuan = tarif.harga_fuso
            elif jenis_armada == 'Tronton':
                harga_satuan = tarif.harga_tronton
            elif jenis_armada in ['Trailer 20 Feet', 'Trailer 40 Feet']:
                harga_satuan = tarif.harga_trailer
                
            total_harga = harga_satuan * jumlah_unit
            
        new_order = Order(user_id=session['user_id'], detail_barang=detail, 
                          jenis_layanan=jenis_layanan, rute=rute, 
                          jenis_armada=jenis_armada, jumlah_unit=jumlah_unit, 
                          total_harga=total_harga)
        db.session.add(new_order)
        db.session.commit()
        return redirect(url_for('orders'))
    
    if session['role'] == 'admin':
        # Set default tab 'belum_bayar' jika parameter tab kosong
        if not request.args.get('tab'):
            return redirect(url_for('orders', tab='belum_bayar'))
        all_orders = Order.query.order_by(Order.id.desc()).all()
    else:
        all_orders = Order.query.filter_by(user_id=session['user_id']).order_by(Order.id.desc()).all()
        
    rutes = db.session.query(Tarif.rute).distinct().all()
    return render_template('orders.html', orders=all_orders, rutes=[r[0] for r in rutes])

@app.route('/orders/validate/<int:id>', methods=['POST'])
@login_required
@admin_required
def validate_order(id):
    order = Order.query.get_or_404(id)
    status = request.form.get('status_order')
    if status in ['Valid', 'Tidak Valid']:
        order.status_order = status
        if status == 'Tidak Valid':
            order.cancelled_by = 'Admin'
            alasan = request.form.get('alasan')
            order.alasan_pembatalan = alasan if alasan else 'Ditolak oleh Admin'
        db.session.commit()
    return redirect(url_for('orders', tab='history' if status == 'Valid' else 'dibatalkan'))

@app.route('/admin/order/<int:order_id>/validasi_pembayaran', methods=['POST'])
@login_required
@admin_required
def validasi_pembayaran(order_id):
    order = Order.query.get_or_404(order_id)
    order.status_pembayaran = 'Lunas'
    db.session.commit()
    flash('Pembayaran berhasil divalidasi', 'success')
    return redirect(url_for('orders', tab='lunas'))

@app.route('/admin/order/<int:order_id>/tolak', methods=['POST'])
@login_required
@admin_required
def tolak_order_admin(order_id):
    order = Order.query.get_or_404(order_id)
    if order.status_pembayaran in ['Belum Bayar', 'Menunggu Pembayaran', 'Menunggu Validasi', 'Lunas']:
        order.status_pembayaran = 'Dibatalkan'
        order.status_order = 'Tidak Valid'
        order.cancelled_by = 'Admin'
        order.alasan_pembatalan = f"Dibatalkan Admin: {request.form.get('alasan')}"
        db.session.commit()
        flash('Pesanan berhasil ditolak.', 'success')
    else:
        flash('Pesanan tidak dapat ditolak pada tahap ini.', 'error')
    return redirect(url_for('orders', tab='dibatalkan'))

@app.route('/order/<int:order_id>/konfirmasi_bayar', methods=['POST'])
@login_required
def konfirmasi_bayar(order_id):
    order = Order.query.get_or_404(order_id)
    if session.get('role') != 'customer' or order.user_id != session['user_id']:
        flash('Akses ditolak.', 'error')
        return redirect(url_for('orders'))
        
    order.status_pembayaran = 'Menunggu Validasi'
    db.session.commit()
    flash('Menunggu validasi admin', 'success')
    return redirect(url_for('orders'))

@app.route('/order/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    if session.get('role') != 'customer' or order.user_id != session['user_id']:
        flash('Akses ditolak.', 'error')
        return redirect(url_for('orders'))
        
    if order.status_order != 'Pending':
        flash('Hanya pesanan yang belum diproses (Pending) yang bisa dibatalkan.', 'error')
        return redirect(url_for('orders'))
        
    alasan = request.form.get('alasan')
    order.status_order = 'Tidak Valid'
    order.alasan_pembatalan = alasan
    order.cancelled_by = 'Customer'
    db.session.commit()
    flash('Pesanan berhasil dibatalkan.', 'success')
    return redirect(url_for('orders'))

@app.route('/orders/edit/<int:id>', methods=['POST'])
@login_required
@admin_required
def edit_order_admin(id):
    order = Order.query.get_or_404(id)
    status_pembayaran = request.form.get('status_pembayaran')
    no_resi = request.form.get('no_resi')
    
    if status_pembayaran in ['Belum Bayar', 'Lunas']:
        order.status_pembayaran = status_pembayaran
    if no_resi:
        existing_resi = Order.query.filter(Order.no_resi == no_resi, Order.id != id).first()
        if existing_resi:
            flash('Nomor Resi tersebut sudah digunakan di order lain.', 'error')
            return redirect(url_for('orders'))
        order.no_resi = no_resi
        
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
        
        order_check = Order.query.get(order_id)
        if not order_check or order_check.status_pembayaran != 'Lunas':
            flash('Order belum lunas. Tidak bisa di-assign ke pengiriman.', 'error')
            return redirect(url_for('pengiriman'))
            
        new_pengiriman = Pengiriman(order_id=order_id, driver_nama=driver, armada_id=armada_id)
        db.session.add(new_pengiriman)
        
        armada_dipilih = Armada.query.get(armada_id)
        if armada_dipilih:
            armada_dipilih.status = 'Beroperasi'
            
        db.session.commit()
        return redirect(url_for('pengiriman'))
    
    if session['role'] == 'admin':
        orders_ready = Order.query.filter_by(status_order='Valid', status_pembayaran='Lunas').filter(~Order.pengiriman.has()).all()
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
        rute=request.form.get('rute'),
        harga_cdd=int(request.form.get('harga_cdd') or 0),
        harga_fuso=int(request.form.get('harga_fuso') or 0),
        harga_tronton=int(request.form.get('harga_tronton') or 0),
        harga_trailer=int(request.form.get('harga_trailer') or 0)
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
    tarif_to_edit.rute = request.form.get('rute')
    tarif_to_edit.harga_cdd = int(request.form.get('harga_cdd') or 0)
    tarif_to_edit.harga_fuso = int(request.form.get('harga_fuso') or 0)
    tarif_to_edit.harga_tronton = int(request.form.get('harga_tronton') or 0)
    tarif_to_edit.harga_trailer = int(request.form.get('harga_trailer') or 0)
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

@app.route('/cek_resi', methods=['GET'])
def cek_resi():
    no_resi = request.args.get('no_resi')
    order = None
    if no_resi:
        order = Order.query.filter_by(no_resi=no_resi).first()
        if not order:
            flash('Nomor Resi tidak ditemukan.', 'error')
            
    return render_template('cek_resi.html', order=order, no_resi=no_resi)

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
