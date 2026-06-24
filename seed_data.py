import os
import django

# Configure Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from master.models import Party, Item, IncomingMaster, IncomingDetail

def seed():
    # Clean existing data to avoid primary key conflicts (in child-parent order)
    IncomingDetail.objects.all().delete()
    IncomingMaster.objects.all().delete()
    Item.objects.all().delete()
    Party.objects.all().delete()
    print("Cleaned existing database records.")

    # 1. Seed Parties
    parties = [
        Party(
            partyname="Himalayan Icy Fruits Ltd",
            add1="Srinagar Highway Crossing",
            add2="Block C, Industrial Estate",
            city="Srinagar",
            gst="01AAAAA1111A1Z1",
            mobile="9876543210",
            email="info@himalayanicy.com",
            opdr=45000.00,
            opcr=0.00,
            remarks="Premium apple grower and cold room lessee."
        ),
        Party(
            partyname="Pacific Marine Exporters",
            add1="Port Road Jetty No. 4",
            add2="Seafood Processing Zone",
            city="Kochi",
            gst="32BBBBB2222B1Z2",
            mobile="9446012345",
            email="logistics@pacificmarine.co",
            opdr=0.00,
            opcr=68250.50,
            remarks="Major seafood buyer. Holds long-term storage agreements."
        ),
        Party(
            partyname="Deccan Agro Distributors",
            add1="Marketyard Gate No. 2",
            add2=None,
            city="Pune",
            gst="27CCCCC3333C1Z3",
            mobile="9822098765",
            email="contact@deccanagro.org",
            opdr=12800.00,
            opcr=0.00,
            remarks="Vegetable distributor. Operates weekly logistics drop-offs."
        ),
        Party(
            partyname="Punjab Farms Logistics",
            add1="GT Road Bypass",
            add2="Opposite Grain Market",
            city="Amritsar",
            gst="03DDDDD4444D1Z4",
            mobile="9814012345",
            email="punjabfarms@gmail.com",
            opdr=0.00,
            opcr=15000.00,
            remarks="Regular supplier of potato stocks."
        ),
    ]
    Party.objects.bulk_create(parties)
    print("Successfully seeded 4 premium sample party profiles!")

    # 2. Seed Items
    items = [
        Item(
            itemname="Golden Apples",
            mode_of_change="Monthly",
            storage_charge=55.00
        ),
        Item(
            itemname="Frozen Green Peas",
            mode_of_change="Monthly",
            storage_charge=45.00
        ),
        Item(
            itemname="Cold-Stored Potatoes",
            mode_of_change="Monthly",
            storage_charge=25.00
        ),
        Item(
            itemname="Alphonso Mango",
            mode_of_change="Yearly",
            storage_charge=1800.00
        )
    ]
    Item.objects.bulk_create(items)
    print("Successfully seeded 4 premium sample item configurations!")

    # 3. Seed Incoming Stocks (Master-Detail)
    master1 = IncomingMaster.objects.create(
        incomingno="REC-001",
        party=Party.objects.get(partyname="Himalayan Icy Fruits Ltd"),
        incoming_date="2026-06-08",
        lotno="LOT-101",
        store_code="REC-001-Golden Apples-500.00-08-06-2026"
    )
    IncomingDetail.objects.create(
        incoming_master=master1,
        item=Item.objects.get(itemname="Golden Apples"),
        mode="Monthly",
        qty=500.00,
        rate=55.00,
        store_charge=27500.00
    )
    IncomingDetail.objects.create(
        incoming_master=master1,
        item=Item.objects.get(itemname="Cold-Stored Potatoes"),
        mode="Monthly",
        qty=200.00,
        rate=25.00,
        store_charge=5000.00
    )

    master2 = IncomingMaster.objects.create(
        incomingno="REC-002",
        party=Party.objects.get(partyname="Pacific Marine Exporters"),
        incoming_date="2026-06-08",
        lotno="LOT-102",
        store_code="REC-002-Alphonso Mango-120.00-08-06-2026"
    )
    IncomingDetail.objects.create(
        incoming_master=master2,
        item=Item.objects.get(itemname="Alphonso Mango"),
        mode="Yearly",
        qty=120.00,
        rate=1800.00,
        store_charge=216000.00
    )
    
    print("Successfully seeded sample Incoming Stock receipt transactions (Master-Detail)!")

if __name__ == '__main__':
    django.setup()
    seed()
