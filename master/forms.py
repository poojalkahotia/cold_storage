import re
import json
from decimal import Decimal
from django import forms
from django.db.models import Q
from .models import ClientDetails, Item, HamaliEntry, IncomingMaster, IncomingDetail, FinalYear, GPMaster, GPDetail, Payment

class ClientDetailsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # make opdr/opcr optional in the form
        if 'opdr' in self.fields:
            self.fields['opdr'].required = False
        if 'opcr' in self.fields:
            self.fields['opcr'].required = False
        if not self.instance.pk:
            if 'opdr' in self.fields:
                self.fields['opdr'].initial = None
            if 'opcr' in self.fields:
                self.fields['opcr'].initial = None

    class Meta:
        model = ClientDetails
        fields = [
            'client_name', 'address', 'area', 'client_type',
            'phone', 'mobile', 'opdr', 'opcr', 'crlimit', 'crdays'
        ]
        widgets = {
            'client_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control form-textarea', 'rows': 3}),
            'area': forms.TextInput(attrs={'class': 'form-control'}),
            'client_type': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'opdr': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'opcr': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'crlimit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'crdays': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        if mobile:
            # Strip spaces, dashes, or parentheses
            mobile = re.sub(r'[\s\-\(\)]', '', mobile)
            if not mobile.isdigit():
                raise forms.ValidationError("Mobile number must contain digits only.")
            if len(mobile) < 10 or len(mobile) > 12:
                raise forms.ValidationError("Mobile number should be between 10 to 12 digits.")
        return mobile or ''

    def clean_address(self):
        address = self.cleaned_data.get('address')
        return address or ''

    def clean_area(self):
        area = self.cleaned_data.get('area')
        return area or ''

    def clean_client_type(self):
        client_type = self.cleaned_data.get('client_type')
        return client_type or ''

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        return phone or ''

    def clean_opdr(self):
        opdr = self.cleaned_data.get('opdr')
        if opdr is None:
            return 0
        if opdr < 0:
            raise forms.ValidationError("Opening Debit balance cannot be negative.")
        return opdr

    def clean_opcr(self):
        opcr = self.cleaned_data.get('opcr')
        if opcr is None:
            return 0
        if opcr < 0:
            raise forms.ValidationError("Opening Credit balance cannot be negative.")
        return opcr

    def clean(self):
        cleaned_data = super().clean()
        opdr = cleaned_data.get('opdr') or 0
        opcr = cleaned_data.get('opcr') or 0

        # An account shouldn't have both initial debit and credit balances
        if opdr > 0 and opcr > 0:
            error_msg = "A client can only have either an opening Debit OR Credit balance, not both."
            self.add_error('opdr', error_msg)
            self.add_error('opcr', error_msg)

        return cleaned_data


class ItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['storage_charge'].initial = None

    class Meta:
        model = Item
        fields = ['itemname', 'mode_of_change', 'storage_charge']
        widgets = {
            'itemname': forms.TextInput(attrs={'class': 'form-control'}),
            'mode_of_change': forms.Select(attrs={'class': 'form-control'}),
            'storage_charge': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }

    def clean_storage_charge(self):
        storage_charge = self.cleaned_data.get('storage_charge')
        if storage_charge is not None and storage_charge < 0:
            raise forms.ValidationError("Storage charge cannot be negative.")
        return storage_charge


class HamaliEntryForm(forms.ModelForm):
    class Meta:
        model = HamaliEntry
        fields = [
            'entry_date', 'party', 'item', 'hamali_type',
            'rate', 'qty', 'amount', 'lot_no', 'location', 'remark'
        ]
        widgets = {
            'entry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'party': forms.Select(attrs={
                'class': 'form-control select2-client-details',
                'data-placeholder': 'Search party by name...'
            }),
            'item': forms.Select(attrs={
                'class': 'form-control select2-client-details',
                'data-placeholder': 'Search item by name...'
            }),
            'hamali_type': forms.TextInput(attrs={'class': 'form-control'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control hamali-rate', 'step': '0.01', 'min': '0.01'}),
            'qty': forms.NumberInput(attrs={'class': 'form-control hamali-qty', 'step': '0.01', 'min': '0.01'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'lot_no': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'remark': forms.Textarea(attrs={'class': 'form-control form-textarea', 'rows': 3}),
        }

    def clean_rate(self):
        rate = self.cleaned_data.get('rate')
        if rate is None or rate <= Decimal('0.00'):
            raise forms.ValidationError("Rate must be greater than zero.")
        return rate

    def clean_qty(self):
        qty = self.cleaned_data.get('qty')
        if qty is None or qty <= Decimal('0.00'):
            raise forms.ValidationError("Qty must be greater than zero.")
        return qty

    def clean(self):
        cleaned_data = super().clean()
        rate = cleaned_data.get('rate')
        qty = cleaned_data.get('qty')
        if rate is not None and qty is not None:
            cleaned_data['amount'] = rate * qty
        return cleaned_data

    def save(self, commit=True):
        self.instance.amount = self.cleaned_data.get('amount') or Decimal('0.00')
        return super().save(commit=commit)


class IncomingMasterForm(forms.ModelForm):
    details_data = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = IncomingMaster
        fields = ['incomingno', 'client_details', 'incoming_date', 'lotno', 'store_code']
        widgets = {
            'incomingno': forms.TextInput(attrs={'class': 'form-control'}),
            'client_details': forms.Select(attrs={'class': 'form-control select2-client-details'}),
            'incoming_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'lotno': forms.TextInput(attrs={'class': 'form-control'}),
            'store_code': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        details_json = cleaned_data.get('details_data')
        
        if not details_json:
            raise forms.ValidationError("You must add at least one item row in the details section.")
            
        try:
            details_list = json.loads(details_json)
        except json.JSONDecodeError:
            raise forms.ValidationError("Invalid details data format.")
            
        if not details_list or len(details_list) == 0:
            raise forms.ValidationError("You must add at least one item row in the details section.")

        cleaned_details = []
        for idx, row in enumerate(details_list, start=1):
            item_name = row.get('itemname')
            mode = row.get('mode')
            qty_str = row.get('qty')
            rate_str = row.get('rate')

            if not item_name:
                raise forms.ValidationError(f"Row {idx}: Item name is required.")
            
            # Check item exists
            if not Item.objects.filter(itemname=item_name).exists():
                raise forms.ValidationError(f"Row {idx}: Item '{item_name}' does not exist.")

            try:
                qty = float(qty_str)
                if qty <= 0:
                    raise ValueError()
            except (ValueError, TypeError):
                raise forms.ValidationError(f"Row {idx}: Quantity must be a positive number.")

            try:
                rate = float(rate_str)
                if rate < 0:
                    raise ValueError()
            except (ValueError, TypeError):
                raise forms.ValidationError(f"Row {idx}: Rate must be a non-negative number.")

            cleaned_details.append({
                'itemname': item_name,
                'mode': mode or 'Monthly',
                'qty': qty,
                'rate': rate,
                'store_charge': qty * rate
            })

        cleaned_data['cleaned_details'] = cleaned_details
        return cleaned_data


class FinalYearForm(forms.ModelForm):
    class Meta:
        model = FinalYear
        fields = ['startdate', 'enddate']
        widgets = {
            'startdate': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'enddate': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        startdate = cleaned_data.get('startdate')
        enddate = cleaned_data.get('enddate')

        if startdate and enddate:
            if enddate <= startdate:
                raise forms.ValidationError("End date must be strictly after the start date.")
            
            # Check for overlapping financial years
            overlapping = FinalYear.objects.filter(
                Q(startdate__lte=enddate) & Q(enddate__gte=startdate)
            )
            # If editing, exclude the current instance
            if self.instance and self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)
                
            if overlapping.exists():
                raise forms.ValidationError("This financial year date range overlaps with an existing configured year.")
                
        return cleaned_data


class GPMasterForm(forms.ModelForm):
    details_data = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = GPMaster
        fields = ['gpno', 'gpdate', 'gptime', 'client_details', 'total', 'remark', 'storage_location', 'recon']
        widgets = {
            'gpno': forms.TextInput(attrs={'class': 'form-control'}),
            'gpdate': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gptime': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'client_details': forms.Select(attrs={'class': 'form-control select2-client-details'}),
            'total': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'remark': forms.TextInput(attrs={'class': 'form-control'}),
            'storage_location': forms.TextInput(attrs={'class': 'form-control'}),
            'recon': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        details_json = cleaned_data.get('details_data')
        
        if not details_json:
            raise forms.ValidationError("You must add at least one item row in the details section.")
            
        try:
            details_list = json.loads(details_json)
        except json.JSONDecodeError:
            raise forms.ValidationError("Invalid details data format.")
            
        if not details_list or len(details_list) == 0:
            raise forms.ValidationError("You must add at least one item row in the details section.")

        cleaned_details = []
        calculated_total = 0.00
        for idx, row in enumerate(details_list, start=1):
            item_name = row.get('itemname')
            qty_str = row.get('qty')

            if not item_name:
                raise forms.ValidationError(f"Row {idx}: Item name is required.")
            
            # Check item exists
            if not Item.objects.filter(itemname=item_name).exists():
                raise forms.ValidationError(f"Row {idx}: Item '{item_name}' does not exist.")

            try:
                qty = float(qty_str)
                if qty <= 0:
                    raise ValueError()
            except (ValueError, TypeError):
                raise forms.ValidationError(f"Row {idx}: Quantity must be a positive number.")

            calculated_total += qty
            cleaned_details.append({
                'itemname': item_name,
                'qty': qty
            })

        cleaned_data['cleaned_details'] = cleaned_details
        cleaned_data['total'] = calculated_total
        return cleaned_data


class PaymentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['incoming_no'].empty_label = "-- Choose Incoming No --"
        self.fields['incoming_no'].required = False

    class Meta:
        model = Payment
        fields = ['paymentno', 'date', 'client_details', 'amount', 'mode_of_payment', 'bank_name', 'cheque_no', 'cheque_date', 'remark', 'incoming_no']
        widgets = {
            'paymentno': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'client_details': forms.Select(attrs={'class': 'form-control select2-client-details'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'mode_of_payment': forms.Select(attrs={'class': 'form-select'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'cheque_no': forms.TextInput(attrs={'class': 'form-control'}),
            'cheque_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'remark': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'incoming_no': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        mode_of_payment = cleaned_data.get('mode_of_payment')
        if mode_of_payment == 'Bank':
            bank_name = cleaned_data.get('bank_name')
            cheque_no = cleaned_data.get('cheque_no')
            cheque_date = cleaned_data.get('cheque_date')
            
            if not bank_name:
                self.add_error('bank_name', "Bank name is required when mode of payment is Bank.")
            if not cheque_no:
                self.add_error('cheque_no', "Cheque number is required when mode of payment is Bank.")
            if not cheque_date:
                self.add_error('cheque_date', "Cheque date is required when mode of payment is Bank.")
        else:
            cleaned_data['bank_name'] = None
            cleaned_data['cheque_no'] = None
            cleaned_data['cheque_date'] = None
        return cleaned_data


