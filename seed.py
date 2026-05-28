import random
import string
from datetime import datetime
from faker import Faker
from app import app, db, User, Tarif, Armada, Order, Pengiriman
from werkzeug.security import generate_password_hash

# Inisialisasi Faker untuk lokal Indonesia
fake = Faker('id_ID')

def seed_database():
    """
    Fungsi untuk mengisi database dengan data dummy.
    """
    with app.app_context():
        # Cek dan tambahkan kolom jika belum ada di database
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        if inspector.has_table('orders'):
            columns = [col['name'] for col in inspector.get_columns('orders')]
            if 'tanggal_order' not in columns:
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE orders ADD COLUMN tanggal_order DATETIME DEFAULT CURRENT_TIMESTAMP"))
                    conn.commit()

        print("Membaca data dari database...")

        # Users
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            print("Membuat akun Admin default...")
            default_admin = User(username='admin', password=generate_password_hash('admin'), role='admin')
            db.session.add(default_admin)
            db.session.commit()

        customers = User.query.filter_by(role='customer').all()
        if not customers:
            print("Membuat dummy Customers...")
            dummy_users = []
            default_password = generate_password_hash('password')
            for _ in range(10):
                customer = User(
                    username=fake.user_name(),
                    password=default_password, 
                    role='customer'
                )
                dummy_users.append(customer)
            db.session.add_all(dummy_users)
            db.session.commit()
            customers = User.query.filter_by(role='customer').all()

        # Orders
        print("Membuat data Orders...")
        all_tarifs = Tarif.query.all()
        if not all_tarifs:
            print("Data Tarif kosong! Harap import atau tambahkan data Tarif di database.")
            return
            
        orders = []
        for _ in range(30):
            customer = random.choice(customers)
            tarif_route = random.choice(all_tarifs)
            
            jenis_armada = random.choice(['CDD', 'Fuso', 'Tronton', 'Trailer 20 Feet', 'Trailer 40 Feet'])
            jumlah_unit = random.randint(1, 3)

            harga_satuan = 0
            if jenis_armada == 'CDD':
                harga_satuan = tarif_route.harga_cdd
            elif jenis_armada == 'Fuso':
                harga_satuan = tarif_route.harga_fuso
            elif jenis_armada == 'Tronton':
                harga_satuan = tarif_route.harga_tronton
            elif jenis_armada in ['Trailer 20 Feet', 'Trailer 40 Feet']:
                harga_satuan = tarif_route.harga_trailer

            total_harga = harga_satuan * jumlah_unit
            status_order = random.choice(['Pending', 'Valid', 'Tidak Valid'])
            status_pembayaran = 'Lunas' if status_order == 'Valid' else random.choice(['Belum Bayar', 'Lunas'])
            no_resi = f"RESI-{random.randint(100000, 999999)}" if status_pembayaran == 'Lunas' else None

            order = Order(
                user_id=customer.id,
                detail_barang=fake.sentence(nb_words=6),
                jenis_layanan=random.choice(['Cargo', 'Container']),
                rute=tarif_route.rute,
                jenis_armada=jenis_armada,
                jumlah_unit=jumlah_unit,
                total_harga=total_harga,
                status_order=status_order,
                status_pembayaran=status_pembayaran,
                no_resi=no_resi,
                tanggal_order=fake.date_time_between(start_date=datetime(2025, 1, 1), end_date=datetime(2026, 6, 30)),
                alasan_pembatalan=fake.sentence() if status_order == 'Tidak Valid' else None,
                cancelled_by=random.choice(['Customer', 'Admin']) if status_order == 'Tidak Valid' else None
            )
            orders.append(order)
        db.session.add_all(orders)
        db.session.commit()

        # Pengiriman
        print("Membuat data Pengiriman...")
        valid_orders = Order.query.filter_by(status_order='Valid').all()
        available_armadas = Armada.query.filter(Armada.status.in_(['Tersedia', 'Beroperasi'])).all()
        pengirimans = []

        if available_armadas:
            for order in valid_orders:
                # Cek apakah order ini sudah punya data pengiriman
                if order.pengiriman is None:
                    armada_terpilih = random.choice(available_armadas)
                    status_kirim = random.choice(['Penjadwalan', 'Di Perjalanan', 'Terkirim'])
                    epod = None
                    if status_kirim == 'Terkirim':
                        epod = f"POD-{fake.lexify(text='??????').upper()}"
                        armada_terpilih.status = 'Tersedia'
                    else:
                        armada_terpilih.status = 'Beroperasi'

                    pengiriman = Pengiriman(
                        order_id=order.id,
                        driver_nama=fake.name(),
                        armada_id=armada_terpilih.id,
                        status_pengiriman=status_kirim,
                        epod_ref=epod
                    )
                    pengirimans.append(pengiriman)
        
        if pengirimans:
            db.session.add_all(pengirimans)
            db.session.commit()        
if __name__ == '__main__':
    seed_database()