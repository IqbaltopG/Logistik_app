import csv
import os
from app import app, db, Tarif

def clean_price(value):
    """Membersihkan format harga seperti Rp8.000.000,00 menjadi integer."""
    if value is None:
        return 0
    
    value = value.replace(',00', '').replace('Rp', '').replace('.', '').strip()
    
    try:
        return int(value)
    except ValueError:
        return 0

def import_tarif_from_csv(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' tidak ditemukan.")
        return

    print(f"Membaca data dari {file_path}...")
    
    with app.app_context():
        # Hapus data lama agar selaras dengan CSV baru
        db.session.query(Tarif).delete()
        
        tarifs = {}
        with open(file_path, mode='r', encoding='utf-8') as csv_file:
            reader = csv.reader(csv_file)
            for i, row in enumerate(reader):
                if i < 2: # Skip 2 baris header pertama CSV
                    continue
                
                # Membaca 3 blok tabel yang disusun menyamping (index 0, 6, dan 12)
                for offset in [0, 6, 12]:
                    if len(row) > offset + 4:
                        asal = row[offset+2].strip()
                        tujuan = row[offset+3].strip()
                        
                        if not asal or not tujuan:
                            continue
                            
                        rute = f"{asal} - {tujuan}"
                        armada = row[offset+1].strip()
                        harga = clean_price(row[offset+4])
                        
                        if rute not in tarifs:
                            tarifs[rute] = {'cdd': 0, 'fuso': 0, 'tronton': 0, 'trailer': 0}
                            
                        # Ambil nilai harga tertinggi per armada (antisipasi selisih harga muatan)
                        if 'Tronton' in armada:
                            if tarifs[rute]['tronton'] == 0 or harga > tarifs[rute]['tronton']:
                                tarifs[rute]['tronton'] = harga
                        elif 'Trailer' in armada:
                            if tarifs[rute]['trailer'] == 0 or harga > tarifs[rute]['trailer']:
                                tarifs[rute]['trailer'] = harga
            
        tarif_list = []
        for rute, data in tarifs.items():
            # Karena di CSV tidak ada list harga CDD & Fuso, kita kalkulasi proporsional saja dari Tronton
            tronton_price = data['tronton']
            if tronton_price > 0:
                data['cdd'] = int(tronton_price * 0.4)
                data['fuso'] = int(tronton_price * 0.7)
                
            new_tarif = Tarif(
                rute=rute,
                harga_cdd=data['cdd'],
                harga_fuso=data['fuso'],
                harga_tronton=data['tronton'],
                harga_trailer=data['trailer']
            )
            tarif_list.append(new_tarif)
        
        if tarif_list:
            db.session.add_all(tarif_list)
            db.session.commit()
            print(f"Berhasil mengimpor {len(tarif_list)} data rute ke dalam tabel Tarif.")
        else:
            print("Tidak ada data yang valid ditemukan di dalam file CSV.")

if __name__ == '__main__':
    csv_filename = 'SIMLOG TUBES - Sheet1.csv'
    import_tarif_from_csv(csv_filename)