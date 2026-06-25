import json
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Q, Avg
from django.core.paginator import Paginator
from .models import ClientDetails, Item, HamaliEntry, IncomingMaster, IncomingDetail, FinalYear, GPMaster, GPDetail, Payment
from .forms import ClientDetailsForm, ItemForm, HamaliEntryForm, IncomingMasterForm, FinalYearForm, GPMasterForm, PaymentForm

def dashboard(request):
    search_query = request.GET.get('search', '').strip()
    client_details_list = ClientDetails.objects.all()

    if search_query:
        client_details_list = client_details_list.filter(
            Q(client_name__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(mobile__icontains=search_query) |
            Q(gst__icontains=search_query)
        )

    # Aggregates for statistics cards
    stats = {
        'total_clients': client_details_list.count(),
        'total_debit': client_details_list.aggregate(total=Sum('opdr'))['total'] or 0.00,
        'total_credit': client_details_list.aggregate(total=Sum('opcr'))['total'] or 0.00,
    }

    # Pagination: 10 clients per page
    paginator = Paginator(client_details_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'stats': stats,
    }
    return render(request, 'master/dashboard.html', context)

def client_details_create(request):
    if request.method == 'POST':
        form = ClientDetailsForm(request.POST)
        if form.is_valid():
            client_details = form.save()
            messages.success(request, f"Client '{client_details.client_name}' created successfully!")
            return redirect('dashboard')
    else:
        form = ClientDetailsForm()
    
    return render(request, 'master/client_details_form.html', {
        'form': form,
        'title': 'Add New Client',
        'button_text': 'Save Client'
    })

def client_details_update(request, pk):
    client_details = get_object_or_404(ClientDetails, pk=pk)
    if request.method == 'POST':
        form = ClientDetailsForm(request.POST, instance=client_details)
        if form.is_valid():
            form.save()
            messages.success(request, f"Client '{client_details.client_name}' updated successfully!")
            return redirect('dashboard')
    else:
        form = ClientDetailsForm(instance=client_details)
    
    return render(request, 'master/client_details_form.html', {
        'form': form,
        'title': 'Edit Client',
        'button_text': 'Update Client'
    })

def client_details_delete(request, pk):
    if request.method == 'POST':
        client_details = get_object_or_404(ClientDetails, pk=pk)
        name = client_details.client_name
        client_details.delete()
        return JsonResponse({
            'success': True,
            'message': f"Client '{name}' has been successfully deleted."
        })
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method.'
    }, status=400)


def item_list(request):
    search_query = request.GET.get('search', '').strip()
    items_list = Item.objects.all()

    if search_query:
        items_list = items_list.filter(
            Q(itemname__icontains=search_query) |
            Q(mode_of_change__icontains=search_query)
        )

    # Aggregates for statistics cards
    monthly_items = items_list.filter(mode_of_change='Monthly')
    yearly_items = items_list.filter(mode_of_change='Yearly')
    
    stats = {
        'total_items': items_list.count(),
        'avg_monthly': monthly_items.aggregate(avg=Avg('storage_charge'))['avg'] or 0.00,
        'avg_yearly': yearly_items.aggregate(avg=Avg('storage_charge'))['avg'] or 0.00,
    }

    # Pagination: 10 items per page
    paginator = Paginator(items_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'stats': stats,
    }
    return render(request, 'master/item_list.html', context)


def item_create(request):
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save()
            messages.success(request, f"Item '{item.itemname}' created successfully!")
            return redirect('item_list')
    else:
        form = ItemForm()
    
    return render(request, 'master/item_form.html', {
        'form': form,
        'title': 'Add New Item',
        'button_text': 'Save Item'
    })


def item_update(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f"Item '{item.itemname}' updated successfully!")
            return redirect('item_list')
    else:
        form = ItemForm(instance=item)
    
    return render(request, 'master/item_form.html', {
        'form': form,
        'title': 'Edit Item',
        'button_text': 'Update Item'
    })


def item_delete(request, pk):
    if request.method == 'POST':
        item = get_object_or_404(Item, pk=pk)
        name = item.itemname
        item.delete()
        return JsonResponse({
            'success': True,
            'message': f"Item '{name}' has been successfully deleted."
        })
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method.'
    }, status=400)


def incoming_list(request):
    search_query = request.GET.get('search', '').strip()
    incoming_list = IncomingMaster.objects.all()

    if search_query:
        incoming_list = incoming_list.filter(
            Q(incomingno__icontains=search_query) |
            Q(client_details__client_name__icontains=search_query) |
            Q(lotno__icontains=search_query) |
            Q(store_code__icontains=search_query)
        )

    # Aggregates for statistics cards
    total_qty = IncomingDetail.objects.filter(incoming_master__in=incoming_list).aggregate(total=Sum('qty'))['total'] or 0.00
    total_charges = IncomingDetail.objects.filter(incoming_master__in=incoming_list).aggregate(total=Sum('store_charge'))['total'] or 0.00

    stats = {
        'total_receipts': incoming_list.count(),
        'total_qty': total_qty,
        'total_charges': total_charges,
    }

    # Pagination: 10 receipts per page
    paginator = Paginator(incoming_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'stats': stats,
    }
    return render(request, 'master/incoming_list.html', context)


def incoming_create(request):
    if request.method == 'POST':
        form = IncomingMasterForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Save the master
                    incoming = form.save()
                    
                    # Create details
                    details_to_create = []
                    for row in form.cleaned_data['cleaned_details']:
                        item = Item.objects.get(itemname=row['itemname'])
                        details_to_create.append(IncomingDetail(
                            incoming_master=incoming,
                            item=item,
                            mode=row['mode'],
                            qty=row['qty'],
                            rate=row['rate'],
                            store_charge=row['store_charge']
                        ))
                    IncomingDetail.objects.bulk_create(details_to_create)
                    
                messages.success(request, f"Incoming Stock Receipt '{incoming.incomingno}' saved successfully!")
                return redirect('incoming_list')
            except Exception as e:
                form.add_error(None, f"Error saving transaction: {str(e)}")
    else:
        form = IncomingMasterForm()

    # Pass client details list and items rate dictionary for JS auto-fill
    client_details_list = ClientDetails.objects.all()
    items = Item.objects.all()
    
    # Create rates lookup dictionary: {itemname: {mode: mode, charge: charge}}
    items_dict = {
        item.itemname: {
            'mode': item.mode_of_change,
            'charge': float(item.storage_charge)
        } for item in items
    }
    
    # Create client lookup dictionary: {client_name: {add1: add1, email: email, mobile: mobile}}
    clients_dict = {
        c.client_name: {
            'add1': c.add1,
            'email': c.email or '',
            'mobile': c.mobile
        } for c in client_details_list
    }

    return render(request, 'master/incoming_form.html', {
        'form': form,
        'title': 'Add Stock Receipt',
        'button_text': 'Save Receipt',
        'items_json': json.dumps(items_dict),
        'parties_json': json.dumps(clients_dict),
        'is_edit': False
    })


def incoming_update(request, pk):
    incoming = get_object_or_404(IncomingMaster, pk=pk)
    
    if request.method == 'POST':
        form = IncomingMasterForm(request.POST, instance=incoming)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Save the master
                    incoming = form.save()
                    
                    # Delete old details
                    incoming.details.all().delete()
                    
                    # Recreate details
                    details_to_create = []
                    for row in form.cleaned_data['cleaned_details']:
                        item = Item.objects.get(itemname=row['itemname'])
                        details_to_create.append(IncomingDetail(
                            incoming_master=incoming,
                            item=item,
                            mode=row['mode'],
                            qty=row['qty'],
                            rate=row['rate'],
                            store_charge=row['store_charge']
                        ))
                    IncomingDetail.objects.bulk_create(details_to_create)
                    
                messages.success(request, f"Incoming Stock Receipt '{incoming.incomingno}' updated successfully!")
                return redirect('incoming_list')
            except Exception as e:
                form.add_error(None, f"Error saving transaction: {str(e)}")
    else:
        # Populate initial JSON details for front-end editing
        initial_details = []
        for detail in incoming.details.all():
            initial_details.append({
                'itemname': detail.item.itemname,
                'mode': detail.mode,
                'qty': float(detail.qty),
                'rate': float(detail.rate),
                'store_charge': float(detail.store_charge)
            })
        
        form = IncomingMasterForm(instance=incoming, initial={
            'details_data': json.dumps(initial_details)
        })

    client_details_list = ClientDetails.objects.all()
    items = Item.objects.all()
    
    items_dict = {
        item.itemname: {
            'mode': item.mode_of_change,
            'charge': float(item.storage_charge)
        } for item in items
    }
    
    clients_dict = {
        c.client_name: {
            'add1': c.add1,
            'email': c.email or '',
            'mobile': c.mobile
        } for c in client_details_list
    }

    return render(request, 'master/incoming_form.html', {
        'form': form,
        'title': 'Edit Stock Receipt',
        'button_text': 'Update Receipt',
        'items_json': json.dumps(items_dict),
        'parties_json': json.dumps(clients_dict),
        'is_edit': True
    })


def incoming_delete(request, pk):
    if request.method == 'POST':
        incoming = get_object_or_404(IncomingMaster, pk=pk)
        no = incoming.incomingno
        incoming.delete()
        return JsonResponse({
            'success': True,
            'message': f"Receipt '{no}' has been successfully deleted."
        })
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method.'
    }, status=400)


def finalyear_list(request):
    search_query = request.GET.get('search', '').strip()
    years_list = FinalYear.objects.all()

    if search_query:
        # Search by filtering date strings or years
        years_list = years_list.filter(
            Q(startdate__icontains=search_query) |
            Q(enddate__icontains=search_query)
        )

    stats = {
        'total_years': years_list.count(),
    }

    paginator = Paginator(years_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'stats': stats,
    }
    return render(request, 'master/finalyear_list.html', context)


def finalyear_create(request):
    if request.method == 'POST':
        form = FinalYearForm(request.POST)
        if form.is_valid():
            year = form.save()
            messages.success(request, f"Financial Year '{year}' created successfully!")
            return redirect('finalyear_list')
    else:
        form = FinalYearForm()

    return render(request, 'master/finalyear_form.html', {
        'form': form,
        'title': 'Add Financial Year',
        'button_text': 'Save'
    })


def finalyear_update(request, pk):
    year = get_object_or_404(FinalYear, pk=pk)
    if request.method == 'POST':
        form = FinalYearForm(request.POST, instance=year)
        if form.is_valid():
            form.save()
            messages.success(request, f"Financial Year '{year}' updated successfully!")
            return redirect('finalyear_list')
    else:
        form = FinalYearForm(instance=year)

    return render(request, 'master/finalyear_form.html', {
        'form': form,
        'title': 'Edit Financial Year',
        'button_text': 'Save'
    })


def finalyear_delete(request, pk):
    if request.method == 'POST':
        year = get_object_or_404(FinalYear, pk=pk)
        name = str(year)
        year.delete()
        return JsonResponse({
            'success': True,
            'message': f"Financial Year '{name}' has been successfully deleted."
        })
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method.'
    }, status=400)


def gp_list(request):
    search_query = request.GET.get('search', '').strip()
    gp_list = GPMaster.objects.all()

    if search_query:
        gp_list = gp_list.filter(
            Q(gpno__icontains=search_query) |
            Q(client_details__client_name__icontains=search_query) |
            Q(storage_location__icontains=search_query) |
            Q(recon__icontains=search_query)
        )

    # Aggregates for statistics cards
    total_qty = GPDetail.objects.filter(gp_master__in=gp_list).aggregate(total=Sum('qty'))['total'] or 0.00

    stats = {
        'total_gps': gp_list.count(),
        'total_qty': total_qty,
    }

    # Pagination: 10 per page
    paginator = Paginator(gp_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'stats': stats,
    }
    return render(request, 'master/gp_list.html', context)


def gp_create(request):
    if request.method == 'POST':
        form = GPMasterForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Save GPMaster
                    gp = form.save(commit=False)
                    gp.total = form.cleaned_data['total']
                    gp.save()
                    
                    # Create details
                    details_to_create = []
                    for row in form.cleaned_data['cleaned_details']:
                        item = Item.objects.get(itemname=row['itemname'])
                        details_to_create.append(GPDetail(
                            gp_master=gp,
                            item=item,
                            qty=row['qty']
                        ))
                    GPDetail.objects.bulk_create(details_to_create)
                    
                messages.success(request, f"Gate Pass '{gp.gpno}' saved successfully!")
                return redirect('gp_list')
            except Exception as e:
                form.add_error(None, f"Error saving transaction: {str(e)}")
    else:
        form = GPMasterForm()

    # Pass client details list and items list
    client_details_list = ClientDetails.objects.all()
    items = Item.objects.all()
    
    # Simple items list for grid choice
    items_list = [item.itemname for item in items]
    
    # Create client lookup dictionary for autocomplete search
    clients_dict = {
        c.client_name: {
            'add1': c.add1,
            'email': c.email or '',
            'mobile': c.mobile
        } for c in client_details_list
    }

    return render(request, 'master/gp_form.html', {
        'form': form,
        'title': 'Create Gate Pass',
        'button_text': 'Save Gate Pass',
        'items_json': json.dumps(items_list),
        'parties_json': json.dumps(clients_dict),
        'is_edit': False
    })


def gp_update(request, pk):
    gp = get_object_or_404(GPMaster, pk=pk)
    
    if request.method == 'POST':
        form = GPMasterForm(request.POST, instance=gp)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Save GPMaster
                    gp = form.save(commit=False)
                    gp.total = form.cleaned_data['total']
                    gp.save()
                    
                    # Delete old details
                    gp.details.all().delete()
                    
                    # Recreate details
                    details_to_create = []
                    for row in form.cleaned_data['cleaned_details']:
                        item = Item.objects.get(itemname=row['itemname'])
                        details_to_create.append(GPDetail(
                            gp_master=gp,
                            item=item,
                            qty=row['qty']
                        ))
                    GPDetail.objects.bulk_create(details_to_create)
                    
                messages.success(request, f"Gate Pass '{gp.gpno}' updated successfully!")
                return redirect('gp_list')
            except Exception as e:
                form.add_error(None, f"Error saving transaction: {str(e)}")
    else:
        # Populate initial JSON details for front-end editing
        initial_details = []
        for detail in gp.details.all():
            initial_details.append({
                'itemname': detail.item.itemname,
                'qty': float(detail.qty)
            })
        
        form = GPMasterForm(instance=gp, initial={
            'details_data': json.dumps(initial_details)
        })

    client_details_list = ClientDetails.objects.all()
    items = Item.objects.all()
    
    items_list = [item.itemname for item in items]
    
    clients_dict = {
        c.client_name: {
            'add1': c.add1,
            'email': c.email or '',
            'mobile': c.mobile
        } for c in client_details_list
    }

    return render(request, 'master/gp_form.html', {
        'form': form,
        'title': 'Edit Gate Pass',
        'button_text': 'Update Gate Pass',
        'items_json': json.dumps(items_list),
        'parties_json': json.dumps(clients_dict),
        'is_edit': True
    })


def gp_delete(request, pk):
    if request.method == 'POST':
        gp = get_object_or_404(GPMaster, pk=pk)
        gpno = gp.gpno
        gp.delete()
        return JsonResponse({
            'success': True,
            'message': f"Gate Pass '{gpno}' has been successfully deleted."
        })
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method.'
    }, status=400)


def payment_list(request):
    search_query = request.GET.get('search', '').strip()
    payments_list = Payment.objects.all()

    if search_query:
        payments_list = payments_list.filter(
            Q(paymentno__icontains=search_query) |
            Q(client_details__client_name__icontains=search_query) |
            Q(mode_of_payment__icontains=search_query) |
            Q(incoming_no__incomingno__icontains=search_query)
        )

    # Aggregates for statistics cards
    total_amount = payments_list.aggregate(total=Sum('amount'))['total'] or 0.00

    stats = {
        'total_payments': payments_list.count(),
        'total_amount': total_amount,
    }

    # Pagination: 10 per page
    paginator = Paginator(payments_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'stats': stats,
    }
    return render(request, 'master/payment_list.html', context)


def payment_create(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            try:
                payment = form.save()
                messages.success(request, f"Payment '{payment.paymentno}' saved successfully!")
                return redirect('payment_list')
            except Exception as e:
                form.add_error(None, f"Error saving payment: {str(e)}")
    else:
        form = PaymentForm()

    client_details_list = ClientDetails.objects.all()
    # Create client lookup dictionary for autocomplete search
    clients_dict = {
        c.client_name: {
            'add1': c.add1,
            'email': c.email or '',
            'mobile': c.mobile
        } for c in client_details_list
    }

    return render(request, 'master/payment_form.html', {
        'form': form,
        'title': 'Create Payment',
        'button_text': 'Save',
        'parties_json': json.dumps(clients_dict),
        'is_edit': False
    })


def payment_update(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            try:
                payment = form.save()
                messages.success(request, f"Payment '{payment.paymentno}' updated successfully!")
                return redirect('payment_list')
            except Exception as e:
                form.add_error(None, f"Error updating payment: {str(e)}")
    else:
        form = PaymentForm(instance=payment)

    client_details_list = ClientDetails.objects.all()
    clients_dict = {
        c.client_name: {
            'add1': c.add1,
            'email': c.email or '',
            'mobile': c.mobile
        } for c in client_details_list
    }

    return render(request, 'master/payment_form.html', {
        'form': form,
        'title': 'Edit Payment',
        'button_text': 'Save',
        'parties_json': json.dumps(clients_dict),
        'is_edit': True
    })


def payment_delete(request, pk):
    if request.method == 'POST':
        payment = get_object_or_404(Payment, pk=pk)
        paymentno = payment.paymentno
        payment.delete()
        return JsonResponse({
            'success': True,
            'message': f"Payment '{paymentno}' has been successfully deleted."
        })
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method.'
    }, status=400)


def hamali_entry_list(request):
    search_query = request.GET.get('search', '').strip()
    entries = HamaliEntry.objects.select_related('party', 'item').all()

    if search_query:
        filters = (
            Q(party__client_name__icontains=search_query)
            | Q(item__itemname__icontains=search_query)
            | Q(entry_date__icontains=search_query)
            | Q(hamali_type__icontains=search_query)
        )
        if search_query.isdigit():
            filters |= Q(entry_no=search_query)
        entries = entries.filter(filters)

    stats = {
        'total_entries': entries.count(),
    }

    paginator = Paginator(entries.order_by('-entry_date', '-entry_no'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'stats': stats,
    }
    return render(request, 'master/hamali_entry_list.html', context)


def hamali_entry_create(request):
    if request.method == 'POST':
        form = HamaliEntryForm(request.POST)
        if form.is_valid():
            entry = form.save()
            messages.success(request, f"Hamali entry #{entry.entry_no} saved successfully!")
            return redirect('hamali_entry_list')
    else:
        form = HamaliEntryForm()

    return render(request, 'master/hamali_entry_form.html', {
        'form': form,
        'title': 'Add Hamali Entry',
        'button_text': 'Save Entry'
    })


def hamali_entry_update(request, pk):
    entry = get_object_or_404(HamaliEntry, pk=pk)
    if request.method == 'POST':
        form = HamaliEntryForm(request.POST, instance=entry)
        if form.is_valid():
            entry = form.save()
            messages.success(request, f"Hamali entry #{entry.entry_no} updated successfully!")
            return redirect('hamali_entry_list')
    else:
        form = HamaliEntryForm(instance=entry)

    return render(request, 'master/hamali_entry_form.html', {
        'form': form,
        'title': 'Edit Hamali Entry',
        'button_text': 'Update Entry'
    })


def hamali_entry_delete(request, pk):
    if request.method == 'POST':
        entry = get_object_or_404(HamaliEntry, pk=pk)
        entry_no = entry.entry_no
        entry.delete()
        return JsonResponse({
            'success': True,
            'message': f"Hamali entry #{entry_no} has been successfully deleted."
        })
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method.'
    }, status=400)



