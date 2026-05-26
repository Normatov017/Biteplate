from django.urls import path

from .views import (
    live_floor_plan,
    floor_editor,
    add_floor_table,
    add_floor_decor,
    save_floor_layout,
)

urlpatterns = [

    path(

        '',

        live_floor_plan,

        name='live_floor_plan'

    ),

    path(
        'editor/',
        floor_editor,
        name='floor_editor'
    ),

    path(
        'editor/table/add/',
        add_floor_table,
        name='add_floor_table'
    ),

    path(
        'editor/decor/add/',
        add_floor_decor,
        name='add_floor_decor'
    ),

    path(
        'editor/save/',
        save_floor_layout,
        name='save_floor_layout'
    ),

]
