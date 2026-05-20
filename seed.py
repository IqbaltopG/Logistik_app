import random
import string
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
        print("🔄 Menghapus data lama dan membuat skema baru...")
        db.drop_all()
        db.create_all()

        # === 1. Generate Users ===
        print("👤 Membuat data Users...")
        users = []
        # Admin utama
        admin_user = User(username='admin', password=generate_password_hash('admin'), role='admin')
        users.append(admin_user)
        # 10 Customer
        for _ in range(10):
            customer = User(
                username=fake.user_name(),
                password=generate_password_hash('password'), # Password default untuk semua dummy customer
                role='customer'
            )
            users.append(customer)
        db.session.add_all(users)
        db.session.commit()
        # Ambil hanya customer untuk referensi order
        customers = User.query.filter_by(role='customer').all()

        # === 2. Generate Armada ===
        print("🚚 Membuat data Armada...")
        armadas = []
        for _ in range(15):
            # Membuat plat nomor format Indonesia (contoh: KT 1234 AB)
            plat = f"KT {random.randint(1000, 9999)} {''.join(random.choices(string.ascii_uppercase, k=2))}"
            armada = Armada(
                plat_nomor=plat,
                tipe_armada=random.choice(['Tronton', 'Trailer', 'Dolly']),
                # Model saat ini hanya mendukung 'Tersedia' dan 'Beroperasi'
                status=random.choice(['Tersedia', 'Beroperasi']) 
            )
            armadas.append(armada)
        db.session.add_all(armadas)

        # === 3. Generate Tarif (Kaltim) ===
        print("🗺️ Membuat data Rute & Tarif Kaltim...")
        kaltim_cities = ['Balikpapan', 'Samarinda', 'Bontang', 'Sangatta', 'Tenggarong', 'Penajam', 'Paser', 'Berau']
        tarifs = []
        for _ in range(10):
            kota_asal, kota_tujuan = random.sample(kaltim_cities, 2)
            tarif = Tarif(
                kota_asal=kota_asal,
                kota_tujuan=kota_tujuan,
                harga_dasar=random.randint(300000, 2000000),
                harga_per_kg=random.randint(1000, 5000),
                harga_per_m3=random.randint(50000, 250000)
            )
            tarifs.append(tarif)
        db.session.add_all(tarifs)
        
        # Commit batch pertama
        db.session.commit()

        # === 4. Generate Orders ===
        print("📦 Membuat data Orders...")
        all_tarifs = Tarif.query.all()
        orders = []
        for _ in range(30):
            customer = random.choice(customers)
            tarif_route = random.choice(all_tarifs)
            
            berat = round(random.uniform(10.5, 500.0), 2)
            p = round(random.uniform(0.5, 3.0), 2)
            l = round(random.uniform(0.5, 3.0), 2)
            t = round(random.uniform(0.5, 3.0), 2)
            volume = p * l * t

            # Kalkulasi estimasi harga otomatis
            estimasi_harga = tarif_route.harga_dasar + (berat * tarif_route.harga_per_kg) + (volume * tarif_route.harga_per_m3)

            order = Order(
                user_id=customer.id,
                detail_barang=fake.sentence(nb_words=6),
                tipe_barang=random.choice(['Container', 'Cargo']),
                kota_asal=tarif_route.kota_asal,
                kota_tujuan=tarif_route.kota_tujuan,
                berat_kg=berat,
                dimensi_p=p,
                dimensi_l=l,
                dimensi_t=t,
                estimasi_harga=estimasi_harga,
                status_order=random.choice(['Pending', 'Valid', 'Tidak Valid'])
            )
            orders.append(order)
        db.session.add_all(orders)
        db.session.commit()

        # === 5. Generate Pengiriman (untuk Order 'Valid') ===
        print("🚛 Membuat data Pengiriman untuk order yang valid...")
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