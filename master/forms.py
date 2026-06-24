import re
import json
from django import forms
from django.db.models import Q
from .models import ClientDetails, Item, IncomingMaster, IncomingDetail, FinalYear, GPMaster, GPDetail, Payment

class ClientDetailsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # make opdr/opcr optional in the form if present; we'll primarily use a combined opening balance field
        if 'opdr' in self.fields:
            self.fields['opdr'].required = False
        if 'opcr' in self.fields:
            self.fields['opcr'].required = False
        if not self.instance.pk:
            if 'opdr' in self.fields:
                self.fields['opdr'].initial = None
            if 'opcr' in self.fields:
                self.fields['opcr'].initial = None

        # add helper fields: a single opening balance and its side (Dr/Cr)
        self.fields['opening_balance'] = forms.DecimalField(
            required=False,
            max_digits=12,
            decimal_places=2,
            widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
        )
        self.fields['opening_side'] = forms.ChoiceField(
            required=False,
            choices=[('Dr', 'Dr'), ('Cr', 'Cr')],
            widget=forms.Select(attrs={'class': 'form-select'})
        )

    class Meta:
        model = ClientDetails
        fields = [
            'client_name', 'address', 'area', 'client_type',
            'phone', 'mobile', 'crlimit', 'crdays'
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
        return mobile

    def clean_opdr(self):
        opdr = self.cleaned_data.get('opdr')
        if opdr is not None and opdr < 0:
            raise forms.ValidationError("Opening Debit balance cannot be negative.")
        return opdr

    def clean_opcr(self):
        opcr = self.cleaned_data.get('opcr')
        if opcr is not None and opcr < 0:
            raise forms.ValidationError("Opening Credit balance cannot be negative.")
        return opcr

    def clean(self):
        cleaned_data = super().clean()

        opening_balance = cleaned_data.get('opening_balance')
        opening_side = cleaned_data.get('opening_side')

        opdr = cleaned_data.get('opdr')
        opcr = cleaned_data.get('opcr')

        # If user provided the combined opening_balance, map it to opdr/opcr
        if opening_balance not in (None, ''):
            try:
                val = float(opening_balance)
            except (TypeError, ValueError):
                self.add_error('opening_balance', "Invalid opening balance value.")
                return cleaned_data

            if val < 0:
                self.add_error('opening_balance', "Opening balance cannot be negative.")
                return cleaned_data

            if opening_side == 'Cr':
                cleaned_data['opcr'] = val
                cleaned_data['opdr'] = 0
            else:
                cleaned_data['opdr'] = val
                cleaned_data['opcr'] = 0
        else:
            # normalize None to 0 for validation
            opdr = opdr or 0
            opcr = opcr or 0

            if opdr > 0 and opcr > 0:
                error_msg = "A client can only have either an opening Debit OR Credit balance, not both."
                self.add_error('opdr', error_msg)
                self.add_error('opcr', error_msg)

        return cleaned_data

    def save(self, commit=True):
        # Map opening_balance/opening_side into model fields opdr/opcr before saving
        instance = super().save(commit=False)
        opening_balance = self.cleaned_data.get('opening_balance')
        opening_side = self.cleaned_data.get('opening_side')

        if opening_balance not in (None, ''):
            val = float(opening_balance)
            if opening_side == 'Cr':
                instance.opcr = val
                instance.opdr = 0
            else:
                instance.opdr = val
                instance.opcr = 0
        else:
            # default to zeros if not provided
            instance.opdr = getattr(instance, 'opdr', 0) or 0
            instance.opcr = getattr(instance, 'opcr', 0) or 0

        if commit:
            instance.save()
        return instance


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


class IncomingMasterForm(forms.ModelForm):
    details_data = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = IncomingMaster
        fields = ['incomingno', 'client_details', 'incoming_date', 'lotno', 'store_code']
        widgets = {
            'incomingno': forms.TextInput(attrs={'class': 'form-control'}),
            'client_details': forms.Select(attrs={'class': 'form-control'}),
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
            'client_details': forms.Select(attrs={'class': 'form-control'}),
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
            'client_details': forms.Select(attrs={'class': 'form-control'}),
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


