from django.db import models
from django.utils import timezone

class ClientDetails(models.Model):
    client_name = models.CharField(max_length=200, primary_key=True, db_column='partyname', verbose_name="Name")
    address = models.TextField(blank=True, null=True, verbose_name="Address")
    area = models.CharField(max_length=100, blank=True, null=True, verbose_name="Area")
    client_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="Client Type")
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="Phone")
    mobile = models.CharField(max_length=15, blank=True, null=True, verbose_name="Mobile")
    opdr = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="OpDr")
    opcr = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="OpCr")
    crlimit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="CrLimit")
    crdays = models.IntegerField(default=0, verbose_name="CrDays")

    class Meta:
        verbose_name = "Client Details"
        verbose_name_plural = "Client Details"
        db_table = 'master_clientdetails'
        ordering = ['client_name']

    def __str__(self):
        return self.client_name

    @property
    def add1(self):
        return self.address or ''

    @property
    def add2(self):
        return ''

    @property
    def city(self):
        return self.area or ''

    @property
    def gst(self):
        return self.client_type or ''

    @property
    def email(self):
        return ''

    @property
    def remarks(self):
        return ''


class Item(models.Model):
    itemname = models.CharField(max_length=200, primary_key=True, verbose_name="Item Name")
    mode_of_change = models.CharField(
        max_length=10,
        choices=[('Monthly', 'Monthly'), ('Yearly', 'Yearly')],
        default='Monthly',
        verbose_name="Mode of Change"
    )
    storage_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Storage Charge"
    )

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Items"
        ordering = ['itemname']

    def __str__(self):
        return self.itemname


class HamaliEntry(models.Model):
    entry_no = models.AutoField(primary_key=True, verbose_name="Entry No")
    entry_date = models.DateField(default=timezone.now, verbose_name="Entry Date")
    party = models.ForeignKey(
        ClientDetails,
        on_delete=models.PROTECT,
        related_name='hamali_entries',
        verbose_name='Party'
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        related_name='hamali_entries',
        verbose_name='Item'
    )
    hamali_type = models.CharField(max_length=100, verbose_name="Hamali Type")
    rate = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Rate")
    qty = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Qty")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Amount")
    lot_no = models.CharField(max_length=100, blank=True, verbose_name="Lot No")
    location = models.CharField(max_length=100, blank=True, verbose_name="Location")
    remark = models.TextField(blank=True, verbose_name="Remark")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Hamali Entry"
        verbose_name_plural = "Hamali Entries"
        ordering = ['-entry_date', '-entry_no']

    def __str__(self):
        return f"Hamali #{self.entry_no}"

    def save(self, *args, **kwargs):
        if self.rate is not None and self.qty is not None:
            self.amount = self.rate * self.qty
        super().save(*args, **kwargs)


class IncomingMaster(models.Model):
    incomingno = models.CharField(max_length=100, primary_key=True, verbose_name="Incoming No")
    client_details = models.ForeignKey(ClientDetails, on_delete=models.CASCADE, related_name='incomings', verbose_name="Client Details", db_column='party_id')
    incoming_date = models.DateField(verbose_name="Incoming Date")
    lotno = models.CharField(max_length=100, verbose_name="Lot No")
    store_code = models.CharField(max_length=255, blank=True, null=True, verbose_name="Store Code")

    class Meta:
        verbose_name = "Incoming Master"
        verbose_name_plural = "Incoming Masters"
        ordering = ['-incoming_date']

    def __str__(self):
        return self.incomingno

    @property
    def total_qty(self):
        return sum(detail.qty for detail in self.details.all())

    @property
    def total_charges(self):
        return sum(detail.store_charge for detail in self.details.all())

    @property
    def items_count(self):
        return self.details.count()



class IncomingDetail(models.Model):
    incoming_master = models.ForeignKey(IncomingMaster, on_delete=models.CASCADE, related_name='details')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='incoming_details', verbose_name="Item")
    mode = models.CharField(max_length=20, verbose_name="Mode")
    qty = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Qty")
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Rate")
    store_charge = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Store Charge")

    class Meta:
        verbose_name = "Incoming Detail"
        verbose_name_plural = "Incoming Details"

    def __str__(self):
        return f"{self.incoming_master.incomingno} - {self.item.itemname}"


class FinalYear(models.Model):
    startdate = models.DateField(verbose_name="Start Date")
    enddate = models.DateField(verbose_name="End Date")

    class Meta:
        verbose_name = "Final Year"
        verbose_name_plural = "Final Years"
        ordering = ['-startdate']

    def __str__(self):
        return f"{self.startdate.strftime('%d %b %Y')} to {self.enddate.strftime('%d %b %Y')}"


class GPMaster(models.Model):
    gpno = models.CharField(max_length=100, primary_key=True, verbose_name="GP No")
    gpdate = models.DateField(verbose_name="GP Date")
    gptime = models.TimeField(verbose_name="GP Time")
    client_details = models.ForeignKey(ClientDetails, on_delete=models.CASCADE, related_name='gatepasses', verbose_name="Client Details", db_column='client_name_id')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Total Qty")
    remark = models.CharField(max_length=255, blank=True, null=True, verbose_name="Remark")
    storage_location = models.CharField(max_length=255, blank=True, null=True, verbose_name="Storage Location")
    recon = models.CharField(max_length=100, blank=True, null=True, verbose_name="Rec No")

    class Meta:
        verbose_name = "GP Master"
        verbose_name_plural = "GP Masters"
        ordering = ['-gpdate', '-gptime']

    def __str__(self):
        return self.gpno


class GPDetail(models.Model):
    gp_master = models.ForeignKey(GPMaster, on_delete=models.CASCADE, related_name='details', verbose_name="GP Master")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='gp_details', verbose_name="Item")
    qty = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Qty")

    class Meta:
        verbose_name = "GP Detail"
        verbose_name_plural = "GP Details"

    def __str__(self):
        return f"{self.gp_master.gpno} - {self.item.itemname}"


class Payment(models.Model):
    paymentno = models.CharField(max_length=100, primary_key=True, verbose_name="Payment No")
    date = models.DateField(verbose_name="Date")
    client_details = models.ForeignKey(ClientDetails, on_delete=models.CASCADE, related_name='payments', verbose_name="Client Details", db_column='party_id')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Amount")
    mode_of_payment = models.CharField(
        max_length=50,
        choices=[('Cash', 'Cash'), ('Bank', 'Bank')],
        default='Cash',
        verbose_name="Mode of Payment"
    )
    bank_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Name of Bank")
    cheque_no = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cheque No")
    cheque_date = models.DateField(blank=True, null=True, verbose_name="Cheque Date")
    remark = models.TextField(blank=True, null=True, verbose_name="Remark")
    incoming_no = models.ForeignKey(IncomingMaster, on_delete=models.SET_NULL, blank=True, null=True, related_name='payments', verbose_name="Incoming No")

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ['-date', 'paymentno']

    def __str__(self):
        return self.paymentno



