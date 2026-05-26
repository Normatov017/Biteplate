import json

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from orders.models import Table
from .models import FloorDecor


def live_floor_plan(request):

    tables = Table.objects.all()

    return render(

        request,

        'floorplan/live_floor.html',

        {

            'tables': tables

        }

    )


def floor_editor(request):

    tables = Table.objects.filter(
        is_active=True
    ).exclude(
        table_number=0
    ).order_by(
        'table_number'
    )

    decors = FloorDecor.objects.all().order_by(
        'id'
    )

    return render(
        request,
        'floorplan/editor.html',
        {
            'tables': tables,
            'decors': decors,
        }
    )


@require_POST
def add_floor_table(request):

    last_table = Table.objects.exclude(
        table_number=0
    ).order_by(
        '-table_number'
    ).first()

    next_number = 1

    if last_table:

        next_number = last_table.table_number + 1

    Table.objects.create(
        table_number=next_number,
        seats=4,
        status='free',
        assigned_waiter='POS',
        pos_x=120,
        pos_y=120,
        pos_width=120,
        pos_height=90
    )

    return redirect(
        'floor_editor'
    )


@require_POST
def add_floor_decor(request):

    decor_type = request.POST.get(
        'decor_type',
        'plant'
    )

    label = request.POST.get(
        'label',
        ''
    )

    FloorDecor.objects.create(
        decor_type=decor_type,
        label=label or decor_type.title(),
        pos_x=80,
        pos_y=80,
        pos_width=140,
        pos_height=80
    )

    return redirect(
        'floor_editor'
    )


@require_POST
def save_floor_layout(request):

    payload = json.loads(
        request.body.decode('utf-8')
    )

    for table_data in payload.get('tables', []):

        Table.objects.filter(
            id=table_data.get('id')
        ).update(
            pos_x=int(table_data.get('x', 120)),
            pos_y=int(table_data.get('y', 120)),
            pos_width=int(table_data.get('width', 120)),
            pos_height=int(table_data.get('height', 90)),
        )

    for decor_data in payload.get('decors', []):

        FloorDecor.objects.filter(
            id=decor_data.get('id')
        ).update(
            pos_x=int(decor_data.get('x', 80)),
            pos_y=int(decor_data.get('y', 80)),
            pos_width=int(decor_data.get('width', 140)),
            pos_height=int(decor_data.get('height', 80)),
        )

    return JsonResponse(
        {
            'ok': True
        }
    )
