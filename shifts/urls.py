from django.urls import path

from .views import (

    shift_dashboard,

    clock_in,

    clock_out,

    open_shift,

    close_shift,

    cash_movement,

    shift_report_excel

)

urlpatterns = [

    path(

        '',

        shift_dashboard,

        name='shift_dashboard'

    ),

    path(

        'open/',

        open_shift,

        name='open_shift'

    ),

    path(

        'clock-in/',

        clock_in,

        name='clock_in'

    ),

    path(

        'clock-out/',

        clock_out,

        name='clock_out'

    ),

    path(

        'close/<int:shift_id>/',

        close_shift,

        name='close_shift'

    ),

    path(

        '<int:shift_id>/cash-movement/',

        cash_movement,

        name='cash_movement'

    ),

    path(

        '<int:shift_id>/report.xlsx',

        shift_report_excel,

        name='shift_report_excel'

    ),

]
