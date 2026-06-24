import json
from django.test import TestCase
from django.urls import reverse
from .models import ClientDetails, Item, IncomingMaster, IncomingDetail, FinalYear, GPMaster, GPDetail, Payment
from .forms import ClientDetailsForm, ItemForm, IncomingMasterForm, FinalYearForm, GPMasterForm, PaymentForm

class ClientDetailsModelTests(TestCase):
    def test_create_client_with_client_name_as_primary_key(self):
        # Create a client
        client_details = ClientDetails.objects.create(
            client_name="Reliance Cold Supplies",
            add1="Indiranagar 1st Cross",
            city="Bengaluru",
            mobile="9876543210",
            opdr=1500.00
        )
        # Verify that pk equals client_name
        self.assertEqual(client_details.pk, "Reliance Cold Supplies")
        self.assertEqual(str(client_details), "Reliance Cold Supplies")


class ClientDetailsFormTests(TestCase):
    def test_valid_client_details_form(self):
        data = {
            'client_name': 'Tata Foods',
            'add1': 'Whitefield Main Road',
            'city': 'Bengaluru',
            'mobile': '9876543210',
            'gst': '29AAAAA1111A1Z1',
            'opdr': '500.00',
            'opcr': '0.00',
            'remarks': 'Valid entry'
        }
        form = ClientDetailsForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_mobile_digits(self):
        data = {
            'client_name': 'Tata Foods',
            'add1': 'Whitefield',
            'city': 'Bengaluru',
            'mobile': '98765ABC10',  # contains letters
            'opdr': '0.00',
            'opcr': '0.00'
        }
        form = ClientDetailsForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('mobile', form.errors)
        self.assertEqual(form.errors['mobile'][0], "Mobile number must contain digits only.")

    def test_invalid_mobile_length(self):
        data = {
            'client_name': 'Tata Foods',
            'add1': 'Whitefield',
            'city': 'Bengaluru',
            'mobile': '98765',  # too short
            'opdr': '0.00',
            'opcr': '0.00'
        }
        form = ClientDetailsForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('mobile', form.errors)

    def test_invalid_gstin_format(self):
        data = {
            'client_name': 'Tata Foods',
            'add1': 'Whitefield',
            'city': 'Bengaluru',
            'mobile': '9876543210',
            'gst': '1234567890ABCDE',  # invalid format
            'opdr': '0.00',
            'opcr': '0.00'
        }
        form = ClientDetailsForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('gst', form.errors)

    def test_both_opdr_and_opcr_cannot_be_positive(self):
        data = {
            'client_name': 'Tata Foods',
            'add1': 'Whitefield',
            'city': 'Bengaluru',
            'mobile': '9876543210',
            'opdr': '100.00',
            'opcr': '250.00'  # both positive
        }
        form = ClientDetailsForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('opdr', form.errors)
        self.assertIn('opcr', form.errors)


class ClientDetailsViewsTests(TestCase):
    def setUp(self):
        self.client1 = ClientDetails.objects.create(
            client_name="Frozen Solutions",
            add1="Sector 5",
            city="Noida",
            mobile="9898989898",
            gst="09AAAAA2222A2Z2",
            opdr=2500.50,
            opcr=0.00
        )
        self.client2 = ClientDetails.objects.create(
            client_name="Iceberg Logistics",
            add1="Ring Road",
            city="Delhi",
            mobile="9191919191",
            opdr=0.00,
            opcr=4000.75
        )

    def test_dashboard_view_and_statistics(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Frozen Solutions")
        self.assertContains(response, "Iceberg Logistics")
        
        # Verify aggregates
        stats = response.context['stats']
        self.assertEqual(stats['total_clients'], 2)
        self.assertEqual(float(stats['total_debit']), 2500.50)
        self.assertEqual(float(stats['total_credit']), 4000.75)

    def test_dashboard_search_filter(self):
        response = self.client.get(reverse('dashboard') + '?search=Frozen')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Frozen Solutions")
        self.assertNotContains(response, "Iceberg Logistics")

    def test_client_details_create_view_post(self):
        response = self.client.post(reverse('client_details_create'), {
            'client_name': 'Alpine Veggies',
            'add1': 'Mall Road',
            'city': 'Shimla',
            'mobile': '9876543210',
            'opdr': '0.00',
            'opcr': '0.00'
        })
        self.assertEqual(response.status_code, 302) # redirect to dashboard
        self.assertTrue(ClientDetails.objects.filter(client_name='Alpine Veggies').exists())

    def test_client_details_update_view_post(self):
        update_url = reverse('client_details_update', kwargs={'pk': self.client1.pk})
        response = self.client.post(update_url, {
            'client_name': 'Frozen Solutions',
            'add1': 'New Address 123',
            'city': 'Noida',
            'mobile': '9898989898',
            'opdr': '3000.00',
            'opcr': '0.00'
        })
        self.assertEqual(response.status_code, 302)
        self.client1.refresh_from_db()
        self.assertEqual(float(self.client1.opdr), 3000.00)
        self.assertEqual(self.client1.add1, 'New Address 123')

    def test_client_details_delete_view_ajax_post(self):
        delete_url = reverse('client_details_delete', kwargs={'pk': self.client1.pk})
        response = self.client.post(
            delete_url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'success': True,
            'message': "Client 'Frozen Solutions' has been successfully deleted."
        })
        self.assertFalse(ClientDetails.objects.filter(client_name='Frozen Solutions').exists())


class ItemModelTests(TestCase):
    def test_create_item_with_itemname_as_primary_key(self):
        item = Item.objects.create(
            itemname="Carrots",
            mode_of_change="Monthly",
            storage_charge=12.50
        )
        self.assertEqual(item.pk, "Carrots")
        self.assertEqual(str(item), "Carrots")


class ItemFormTests(TestCase):
    def test_valid_item_form(self):
        data = {
            'itemname': 'Green Peas',
            'mode_of_change': 'Yearly',
            'storage_charge': '150.00'
        }
        form = ItemForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_negative_charge(self):
        data = {
            'itemname': 'Green Peas',
            'mode_of_change': 'Yearly',
            'storage_charge': '-10.00'
        }
        form = ItemForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('storage_charge', form.errors)


class ItemViewsTests(TestCase):
    def setUp(self):
        self.item1 = Item.objects.create(
            itemname="Apples",
            mode_of_change="Monthly",
            storage_charge=20.00
        )
        self.item2 = Item.objects.create(
            itemname="Potatoes",
            mode_of_change="Yearly",
            storage_charge=150.00
        )

    def test_item_list_view_and_statistics(self):
        response = self.client.get(reverse('item_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Apples")
        self.assertContains(response, "Potatoes")
        
        stats = response.context['stats']
        self.assertEqual(stats['total_items'], 2)
        self.assertEqual(float(stats['avg_monthly']), 20.00)
        self.assertEqual(float(stats['avg_yearly']), 150.00)

    def test_item_list_search_filter(self):
        response = self.client.get(reverse('item_list') + '?search=Potatoes')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Potatoes")
        self.assertNotContains(response, "Apples")

    def test_item_create_view_post(self):
        response = self.client.post(reverse('item_create'), {
            'itemname': 'Strawberries',
            'mode_of_change': 'Monthly',
            'storage_charge': '45.00'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Item.objects.filter(itemname='Strawberries').exists())

    def test_item_update_view_post(self):
        update_url = reverse('item_update', kwargs={'pk': self.item1.pk})
        response = self.client.post(update_url, {
            'itemname': 'Apples',
            'mode_of_change': 'Yearly',
            'storage_charge': '250.00'
        })
        self.assertEqual(response.status_code, 302)
        self.item1.refresh_from_db()
        self.assertEqual(self.item1.mode_of_change, 'Yearly')
        self.assertEqual(float(self.item1.storage_charge), 250.00)

    def test_item_delete_view_ajax_post(self):
        delete_url = reverse('item_delete', kwargs={'pk': self.item1.pk})
        response = self.client.post(
            delete_url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'success': True,
            'message': "Item 'Apples' has been successfully deleted."
        })
        self.assertFalse(Item.objects.filter(itemname='Apples').exists())


class IncomingModelTests(TestCase):
    def setUp(self):
        self.client_details = ClientDetails.objects.create(
            client_name="Test Party",
            add1="Test Addr",
            city="Test City",
            mobile="9876543210"
        )
        self.item = Item.objects.create(
            itemname="Test Item",
            mode_of_change="Monthly",
            storage_charge=10.00
        )

    def test_incoming_master_and_detail_creation_and_properties(self):
        master = IncomingMaster.objects.create(
            incomingno="INC-TEST-100",
            client_details=self.client_details,
            incoming_date="2026-06-08",
            lotno="LOT-A",
            store_code="INC-TEST-100-Test Item-100-08-06-2026"
        )
        detail = IncomingDetail.objects.create(
            incoming_master=master,
            item=self.item,
            mode="Monthly",
            qty=100.00,
            rate=12.50,
            store_charge=1250.00
        )
        
        self.assertEqual(master.pk, "INC-TEST-100")
        self.assertEqual(master.items_count, 1)
        self.assertEqual(float(master.total_qty), 100.00)
        self.assertEqual(float(master.total_charges), 1250.00)


class IncomingFormTests(TestCase):
    def setUp(self):
        self.client_details = ClientDetails.objects.create(
            client_name="Test Party",
            add1="Test Addr",
            city="Test City",
            mobile="9876543210"
        )
        self.item = Item.objects.create(
            itemname="Test Item",
            mode_of_change="Monthly",
            storage_charge=10.00
        )

    def test_valid_incoming_form_with_json_details(self):
        details_json = json.dumps([
            {'itemname': 'Test Item', 'mode': 'Monthly', 'qty': '100.00', 'rate': '10.00'}
        ])
        data = {
            'incomingno': 'INC-001',
            'client_details': 'Test Party',
            'incoming_date': '2026-06-08',
            'lotno': 'LOT-100',
            'store_code': 'INC-001-Test Item-100-08-06-2026',
            'details_data': details_json
        }
        form = IncomingMasterForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_form_no_details(self):
        data = {
            'incomingno': 'INC-001',
            'client_details': 'Test Party',
            'incoming_date': '2026-06-08',
            'lotno': 'LOT-100',
            'store_code': '',
            'details_data': '[]'  # empty details
        }
        form = IncomingMasterForm(data=data)
        self.assertFalse(form.is_valid())

    def test_invalid_form_negative_qty(self):
        details_json = json.dumps([
            {'itemname': 'Test Item', 'mode': 'Monthly', 'qty': '-50.00', 'rate': '10.00'}
        ])
        data = {
            'incomingno': 'INC-001',
            'client_details': 'Test Party',
            'incoming_date': '2026-06-08',
            'lotno': 'LOT-100',
            'store_code': '',
            'details_data': details_json
        }
        form = IncomingMasterForm(data=data)
        self.assertFalse(form.is_valid())


class IncomingViewsTests(TestCase):
    def setUp(self):
        self.client_details = ClientDetails.objects.create(
            client_name="Himachal Cold storage",
            add1="Srinagar Highway",
            city="Srinagar",
            mobile="9876543210"
        )
        self.item = Item.objects.create(
            itemname="Apples",
            mode_of_change="Monthly",
            storage_charge=50.00
        )
        self.master1 = IncomingMaster.objects.create(
            incomingno="INC-500",
            client_details=self.client_details,
            incoming_date="2026-06-08",
            lotno="LOT-X",
            store_code="INC-500-Apples-500-08-06-2026"
        )
        self.detail1 = IncomingDetail.objects.create(
            incoming_master=self.master1,
            item=self.item,
            mode="Monthly",
            qty=500.00,
            rate=50.00,
            store_charge=25000.00
        )

    def test_incoming_list_view_and_statistics(self):
        response = self.client.get(reverse('incoming_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "INC-500")
        
        stats = response.context['stats']
        self.assertEqual(stats['total_receipts'], 1)
        self.assertEqual(float(stats['total_qty']), 500.00)
        self.assertEqual(float(stats['total_charges']), 25000.00)

    def test_incoming_list_search_filter(self):
        response = self.client.get(reverse('incoming_list') + '?search=LOT-X')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "INC-500")
        
        response_empty = self.client.get(reverse('incoming_list') + '?search=LOT-Y')
        self.assertNotContains(response_empty, "INC-500")

    def test_incoming_create_view_post(self):
        details_json = json.dumps([
            {'itemname': 'Apples', 'mode': 'Monthly', 'qty': '200.00', 'rate': '50.00'}
        ])
        response = self.client.post(reverse('incoming_create'), {
            'incomingno': 'INC-501',
            'client_details': 'Himachal Cold storage',
            'incoming_date': '2026-06-08',
            'lotno': 'LOT-Y',
            'store_code': 'INC-501-Apples-200-08-06-2026',
            'details_data': details_json
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(IncomingMaster.objects.filter(incomingno='INC-501').exists())
        self.assertEqual(IncomingDetail.objects.filter(incoming_master__incomingno='INC-501').count(), 1)

    def test_incoming_update_view_post(self):
        update_url = reverse('incoming_update', kwargs={'pk': self.master1.pk})
        details_json = json.dumps([
            {'itemname': 'Apples', 'mode': 'Monthly', 'qty': '600.00', 'rate': '60.00'} # modified values
        ])
        response = self.client.post(update_url, {
            'incomingno': 'INC-500',
            'client_details': 'Himachal Cold storage',
            'incoming_date': '2026-06-08',
            'lotno': 'LOT-X-UPDATED',
            'store_code': 'INC-500-Apples-600-08-06-2026',
            'details_data': details_json
        })
        self.assertEqual(response.status_code, 302)
        self.master1.refresh_from_db()
        self.assertEqual(self.master1.lotno, 'LOT-X-UPDATED')
        self.assertEqual(float(self.master1.total_qty), 600.00)
        self.assertEqual(float(self.master1.total_charges), 36000.00)

    def test_incoming_delete_view_ajax_post(self):
        delete_url = reverse('incoming_delete', kwargs={'pk': self.master1.pk})
        response = self.client.post(
            delete_url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'success': True,
            'message': "Receipt 'INC-500' has been successfully deleted."
        })
        self.assertFalse(IncomingMaster.objects.filter(incomingno='INC-500').exists())


class FinalYearTests(TestCase):
    def test_create_final_year(self):
        year = FinalYear.objects.create(
            startdate="2026-04-01",
            enddate="2027-03-31"
        )
        year.refresh_from_db()
        self.assertEqual(str(year), "01 Apr 2026 to 31 Mar 2027")

    def test_form_validation(self):
        # Valid form
        form = FinalYearForm(data={'startdate': '2026-04-01', 'enddate': '2027-03-31'})
        self.assertTrue(form.is_valid())

        # Invalid form (end date before start date)
        form = FinalYearForm(data={'startdate': '2026-04-01', 'enddate': '2026-03-31'})
        self.assertFalse(form.is_valid())
        self.assertIn("End date must be strictly after the start date.", form.non_field_errors())

        # Invalid form (overlapping ranges)
        FinalYear.objects.create(startdate="2026-04-01", enddate="2027-03-31")
        form = FinalYearForm(data={'startdate': '2026-10-01', 'enddate': '2027-09-30'})
        self.assertFalse(form.is_valid())
        self.assertIn("This financial year date range overlaps with an existing configured year.", form.non_field_errors())

    def test_views_and_list(self):
        year = FinalYear.objects.create(startdate="2026-04-01", enddate="2027-03-31")
        
        # Test List View
        response = self.client.get(reverse('finalyear_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "01 April 2026")
        self.assertContains(response, "31 March 2027")

        # Test Create View
        response = self.client.post(reverse('finalyear_create'), {
            'startdate': '2027-04-01',
            'enddate': '2028-03-31'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(FinalYear.objects.filter(startdate='2027-04-01').exists())

        # Test Update View
        update_url = reverse('finalyear_update', kwargs={'pk': year.pk})
        response = self.client.post(update_url, {
            'startdate': '2026-04-01',
            'enddate': '2027-03-15' # modified to not overlap with 2027-04-01
        })
        self.assertEqual(response.status_code, 302)
        year.refresh_from_db()
        self.assertEqual(str(year.enddate), '2027-03-15')

        # Test Delete View
        delete_url = reverse('finalyear_delete', kwargs={'pk': year.pk})
        response = self.client.post(delete_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'success': True,
            'message': "Financial Year '01 Apr 2026 to 15 Mar 2027' has been successfully deleted."
        })
        self.assertFalse(FinalYear.objects.filter(pk=year.pk).exists())


class GatePassTests(TestCase):
    def setUp(self):
        self.client_details = ClientDetails.objects.create(
            client_name="Tata Logistics",
            add1="Whitefield Main Road",
            city="Bengaluru",
            mobile="9876543210"
        )
        self.item = Item.objects.create(
            itemname="Apples",
            mode_of_change="Monthly",
            storage_charge=50.00
        )

    def test_gp_models_creation(self):
        gp = GPMaster.objects.create(
            gpno="GP-6390",
            gpdate="2026-06-23",
            gptime="21:15:00",
            client_details=self.client_details,
            total=100.00,
            remark="Test gate pass",
            storage_location="Warehouse A",
            recon="REC-123"
        )
        detail = GPDetail.objects.create(
            gp_master=gp,
            item=self.item,
            qty=100.00
        )
        self.assertEqual(gp.pk, "GP-6390")
        self.assertEqual(gp.details.count(), 1)
        self.assertEqual(str(gp), "GP-6390")
        self.assertEqual(str(detail), "GP-6390 - Apples")

    def test_gp_form_valid(self):
        details_json = json.dumps([
            {'itemname': 'Apples', 'qty': '150.00'}
        ])
        data = {
            'gpno': 'GP-100',
            'gpdate': '2026-06-23',
            'gptime': '21:15:00',
            'client_details': 'Tata Logistics',
            'total': '150.00',
            'remark': 'Form test',
            'storage_location': 'Warehouse A',
            'recon': 'REC-99',
            'details_data': details_json
        }
        form = GPMasterForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['total'], 150.00)

    def test_gp_form_invalid_no_details(self):
        data = {
            'gpno': 'GP-100',
            'gpdate': '2026-06-23',
            'gptime': '21:15:00',
            'client_details': 'Tata Logistics',
            'total': '0.00',
            'details_data': '[]'
        }
        form = GPMasterForm(data=data)
        self.assertFalse(form.is_valid())

    def test_gp_views_list_create_update_delete(self):
        # Create a GatePass
        response = self.client.post(reverse('gp_create'), {
            'gpno': 'GP-TEST-99',
            'gpdate': '2026-06-23',
            'gptime': '21:15',
            'client_details': 'Tata Logistics',
            'total': '250.00',
            'storage_location': 'Dock 1',
            'recon': 'REC-1234',
            'details_data': json.dumps([{'itemname': 'Apples', 'qty': '250.00'}])
        })
        self.assertEqual(response.status_code, 302) # Redirect to list
        self.assertTrue(GPMaster.objects.filter(gpno='GP-TEST-99').exists())

        # List view
        response = self.client.get(reverse('gp_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'GP-TEST-99')

        # Update view
        gp = GPMaster.objects.get(gpno='GP-TEST-99')
        response = self.client.post(reverse('gp_update', kwargs={'pk': gp.pk}), {
            'gpno': 'GP-TEST-99',
            'gpdate': '2026-06-23',
            'gptime': '21:30',
            'client_details': 'Tata Logistics',
            'total': '400.00',
            'storage_location': 'Dock 2',
            'recon': 'REC-1234-UPDATED',
            'details_data': json.dumps([{'itemname': 'Apples', 'qty': '400.00'}])
        })
        self.assertEqual(response.status_code, 302)
        gp.refresh_from_db()
        self.assertEqual(gp.storage_location, 'Dock 2')
        self.assertEqual(float(gp.total), 400.00)

        # Delete view
        delete_url = reverse('gp_delete', kwargs={'pk': gp.pk})
        response = self.client.post(delete_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'success': True,
            'message': "Gate Pass 'GP-TEST-99' has been successfully deleted."
        })
        self.assertFalse(GPMaster.objects.filter(gpno='GP-TEST-99').exists())


class PaymentTests(TestCase):
    def setUp(self):
        self.client_details = ClientDetails.objects.create(
            client_name="Tata Logistics",
            add1="Whitefield Main Road",
            city="Bengaluru",
            mobile="9876543210"
        )
        self.incoming = IncomingMaster.objects.create(
            incomingno="INC-100",
            client_details=self.client_details,
            incoming_date="2026-06-23",
            lotno="LOT-X"
        )

    def test_payment_model_creation(self):
        payment = Payment.objects.create(
            paymentno="PMT-26",
            date="2026-06-23",
            client_details=self.client_details,
            amount=15000.00,
            mode_of_payment="Bank",
            bank_name="HDFC Bank",
            cheque_no="CHQ9876",
            cheque_date="2026-06-23",
            remark="Paid bank transfer",
            incoming_no=self.incoming
        )
        self.assertEqual(payment.pk, "PMT-26")
        self.assertEqual(float(payment.amount), 15000.00)
        self.assertEqual(payment.bank_name, "HDFC Bank")
        self.assertEqual(payment.cheque_no, "CHQ9876")
        self.assertEqual(str(payment), "PMT-26")

    def test_payment_form_cash_valid(self):
        data = {
            'paymentno': 'PMT-50',
            'date': '2026-06-23',
            'client_details': 'Tata Logistics',
            'amount': '25000.50',
            'mode_of_payment': 'Cash',
            'remark': 'Valid cash details',
            'incoming_no': 'INC-100',
            'bank_name': 'Random Bank',  # should be cleared by clean()
            'cheque_no': '1234',
            'cheque_date': '2026-06-23'
        }
        form = PaymentForm(data=data)
        self.assertTrue(form.is_valid())
        payment = form.save(commit=False)
        self.assertIsNone(payment.bank_name)
        self.assertIsNone(payment.cheque_no)
        self.assertIsNone(payment.cheque_date)

    def test_payment_form_bank_valid(self):
        data = {
            'paymentno': 'PMT-51',
            'date': '2026-06-23',
            'client_details': 'Tata Logistics',
            'amount': '25000.50',
            'mode_of_payment': 'Bank',
            'bank_name': 'ICICI Bank',
            'cheque_no': 'CHQ-888',
            'cheque_date': '2026-06-23',
            'remark': 'Valid bank details',
            'incoming_no': 'INC-100'
        }
        form = PaymentForm(data=data)
        self.assertTrue(form.is_valid())

    def test_payment_form_bank_invalid_missing_fields(self):
        data = {
            'paymentno': 'PMT-52',
            'date': '2026-06-23',
            'client_details': 'Tata Logistics',
            'amount': '25000.50',
            'mode_of_payment': 'Bank',
            'incoming_no': 'INC-100'
        }
        form = PaymentForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('bank_name', form.errors)
        self.assertIn('cheque_no', form.errors)
        self.assertIn('cheque_date', form.errors)

    def test_payment_views_list_create_update_delete(self):
        # Create
        response = self.client.post(reverse('payment_create'), {
            'paymentno': 'PMT-TEST-01',
            'date': '2026-06-23',
            'client_details': 'Tata Logistics',
            'amount': '3500.00',
            'mode_of_payment': 'Bank',
            'bank_name': 'Axis Bank',
            'cheque_no': 'AXIS777',
            'cheque_date': '2026-06-23',
            'remark': 'NEFT transfer',
            'incoming_no': 'INC-100'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Payment.objects.filter(paymentno='PMT-TEST-01').exists())
        pmt = Payment.objects.get(paymentno='PMT-TEST-01')
        self.assertEqual(pmt.bank_name, 'Axis Bank')

        # List
        response = self.client.get(reverse('payment_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PMT-TEST-01')

        # Update
        payment = Payment.objects.get(paymentno='PMT-TEST-01')
        response = self.client.post(reverse('payment_update', kwargs={'pk': payment.pk}), {
            'paymentno': 'PMT-TEST-01',
            'date': '2026-06-23',
            'client_details': 'Tata Logistics',
            'amount': '4200.00',
            'mode_of_payment': 'Bank',
            'bank_name': 'Axis Bank New',
            'cheque_no': 'AXIS888',
            'cheque_date': '2026-06-24',
            'remark': 'NEFT transfer updated',
            'incoming_no': ''
        })
        self.assertEqual(response.status_code, 302)
        payment.refresh_from_db()
        self.assertEqual(float(payment.amount), 4200.00)
        self.assertEqual(payment.bank_name, 'Axis Bank New')
        self.assertEqual(payment.cheque_no, 'AXIS888')
        self.assertIsNone(payment.incoming_no)

        # Delete
        delete_url = reverse('payment_delete', kwargs={'pk': payment.pk})
        response = self.client.post(delete_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'success': True,
            'message': "Payment 'PMT-TEST-01' has been successfully deleted."
        })
        self.assertFalse(Payment.objects.filter(paymentno='PMT-TEST-01').exists())



