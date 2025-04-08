from django.shortcuts import render
from django.shortcuts import render, redirect
from django.db import connections
import json
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from .forms import JournalForm
from django.urls import reverse
import requests


sl = {}


def main(request):
    return render(
        request,
        "diplom/index.html",
    )


def get_journal(request):
    global sl
    up = request.GET.get("up")
    divs = []
    if request.session.session_key is None:
        request.session.create()
    session_key = request.session.session_key
    if str(session_key) not in sl:
        sl[str(session_key)] = {
            "date_end": str(datetime.now().date() + timedelta(days=1)),
            "date_start": str(datetime.now().date() - timedelta(days=30)),
            "div_no": 0,
            "pmd_no": 0,
            "result": 0,
        }
    with connections["miha"].cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT div_no FROM mkadd.passport_material_deviation""",
        )
        divs = cursor.fetchall()
    divs = [i[0] for i in divs]
    if up is not None:
        sl[str(session_key)]["result"] = 0
        sl[str(session_key)]["date_end"] = str(
            datetime.now().date() + timedelta(days=1)
        )
        sl[str(session_key)]["date_start"] = str(
            datetime.now().date() - timedelta(days=30)
        )
        sl[str(session_key)]["div_no"] = 0

    if request.method == "POST":
        sl[str(session_key)]["date_start"] = request.POST.get("date_start")
        sl[str(session_key)]["date_end"] = request.POST.get("date_end")
        sl[str(session_key)]["div_no"] = request.POST.get("div_no")
        sl[str(session_key)]["pmd_no"] = request.POST.get("numberpunkt")
        sl[str(session_key)]["result"] = 0
    if len(str(sl[str(session_key)]["pmd_no"])) == 0:
        sl[str(session_key)]["pmd_no"] = 0

    if request.GET.get("tests") is not None:
        sl[str(session_key)]["result"] = 0
    slov = json.dumps(
        {
            "pmd_no": sl[str(session_key)]["pmd_no"],
            "date_start": sl[str(session_key)]["date_start"],
            "date_end": sl[str(session_key)]["date_end"],
            "department": sl[str(session_key)]["div_no"],
        }
    )
    sortdate = request.GET.get("sortdate")
    if sl[str(session_key)]["result"] == 0:
        with connections["miha"].cursor() as cursor:
            cursor.execute(
                """
                    SELECT mkadd.journal_accounting_permissions(%s)""",
                [slov],
            )
            sl[str(session_key)]["result"] = cursor.fetchall()

        sl[str(session_key)]["result"] = list(sl[str(session_key)]["result"][0])[0][
            "dataset"
        ]
    page_number = request.GET.get("page")
    if page_number is None:
        page_number = 0
    if sl[str(session_key)]["result"] is None:

        context = {
            "page_obj": sl[str(session_key)]["result"],
            "date_start": sl[str(session_key)]["date_start"],
            "date_end": sl[str(session_key)]["date_end"],
            "div_no": sl[str(session_key)]["div_no"],
            "pmd_no": sl[str(session_key)]["pmd_no"],
            "page_number": page_number,
            "divs": divs,
        }
    else:
        if sortdate is not None and sortdate == "True":
            sl[str(session_key)]["result"] = sorted(
                sl[str(session_key)]["result"],
                key=lambda x: datetime.strptime(x["pmd_date_add"], "%Y-%m-%d"),
                reverse=True,
            )
        if sortdate is not None and sortdate == "False":
            sl[str(session_key)]["result"] = sorted(
                sl[str(session_key)]["result"],
                key=lambda x: datetime.strptime(x["pmd_date_add"], "%Y-%m-%d"),
                reverse=False,
            )
        paginator = Paginator(sl[str(session_key)]["result"], 100)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        if page_number is None:
            page_number = 0
        context = {
            "page_obj": page_obj,
            "date_start": sl[str(session_key)]["date_start"],
            "date_end": sl[str(session_key)]["date_end"],
            "div_no": sl[str(session_key)]["div_no"],
            "pmd_no": sl[str(session_key)]["pmd_no"],
            "page_number": page_number,
            "divs": divs,
        }
    return render(request, "diplom/journal.html", context=context)


def create_journal(request, page):
    if request.session.session_key is None:
        request.session.create()
    session_key = request.session.session_key
    if request.method == "POST":
        form = JournalForm(request.POST)
        if form.is_valid():
            try:
                num_sp = request.POST.get("num_sp").split("/")
                to = num_sp[1].split()
                with connections["miha"].cursor() as cursor:
                    cursor.execute(
                        """
                            SELECT pas_id FROM mkadd.passport
                            WHERE pas_no =%s and pas_year=%s and div_no=%s
                            """,
                        [int(num_sp[0]), int(to[1]), int(to[0])],
                    )
                    idpasport = cursor.fetchall()
                if len(idpasport) > 0:
                    idpasport = idpasport[0][0]
                slov = json.dumps(
                    {
                        "div_no": request.POST.get("div_no"),
                        "pmd_no": request.POST.get("num_punct"),
                        "pmd_material": request.POST.get("pmd_material"),
                        "pmd_note_tp": request.POST.get("pmd_note_tp"),
                        "pmd_note_pi": request.POST.get("pmd_note_pi"),
                        "ul_login": request.POST.get("ul_login"),
                        "pmd_responsible": request.POST.get("pmd_responsible"),
                        "IDPasport": idpasport,
                    },
                    ensure_ascii=False,
                )

                with connections["miha"].cursor() as cursor:
                    cursor.execute(
                        """
                            SELECT mkadd.insert_deviere_mtr(%s)""",
                        [slov],
                    )
                    result = cursor.fetchall()
            except Exception as e:
                print(f"Ошибка : {str(e)}")
                form = JournalForm(request.POST)

                context = {"form": form, "eror": True, "page": page}
                return render(request, "diplom/create_journal.html",
                              context=context)
            url = reverse("diplom:journal")
            numberpunkt = request.POST.get("num_punct")
            ur = request.build_absolute_uri(url)
            requests.get(
                url=ur, params={"up": "up"}, cookies={"sessionid": session_key}
            )
            return redirect(f"{url}?sortdate=True#{numberpunkt}")
        return render(request, "diplom/create_journal.html", context=context)

    form = JournalForm()
    context = {"form": form, "eror": False, "page": page}
    return render(request, "diplom/create_journal.html", context=context)


def update_journal(request, pas_id, numberpunkt, page):
    if request.session.session_key is None:
        request.session.create()
    session_key = request.session.session_key
    slov = json.dumps(
        {
            "idpasport": pas_id,
        }
    )
    result = 0
    with connections["miha"].cursor() as cursor:
        cursor.execute(
            """
                SELECT mkadd.journal_permissions(%s)""",
            [slov],
        )
        result = cursor.fetchall()
    result = list(result[0])[0]["dataset"][0]
    context = {
        "result": result,
        "eror": False,
        "numberpunkt": numberpunkt,
        "page": page,
    }
    if request.method == "POST":
        slov = json.dumps(
            {
                "pmd_note_tp": request.POST.get("pmd_note_tp"),
                "pmd_note_pi": request.POST.get("pmd_note_pi"),
                "ul_login": request.POST.get("ul_login"),
                "pmd_responsible": request.POST.get("pmd_responsible"),
                "idpasport": pas_id,
            },
            ensure_ascii=False,
        )
        try:
            with connections["miha"].cursor() as cursor:
                cursor.execute(
                    """
                            SELECT mkadd.update_journal(%s)""",
                    [slov],
                )
                result = cursor.fetchall()
            url = reverse("diplom:journal")
            ur = request.build_absolute_uri(url)
            requests.get(
                url=ur, params={"tests": "tests"},
                cookies={"sessionid": session_key}
            )
            return redirect(f"{url}?page={page}#{numberpunkt}")
        except Exception:
            context["eror"] = True
            return render(request, "diplom/update_journal.html",
                          context=context)
    return render(request, "diplom/update_journal.html", context=context)


def repl(mas):
    for i in range(len(mas)):
        if mas[i] < 200:
            mas[i] = 300


def analytics(request):
    data = [1,2,3,4,5]
    data1 = [23,32,23,32,1]

    div_no = [79,25,12,123,12]
    # with connections["miha"].cursor() as cursor:
    #     cursor.execute(
    #         """
    #         SELECT DISTINCT div_no FROM mkadd.passport_material_deviation""",
    #     )
    #     div_no = cursor.fetchall()

    # div_no = [int(i[0]) for i in div_no]

    # for div in div_no:
    #     with connections["miha"].cursor() as cursor:
    #         cursor.execute(
    #             """
    #                 SELECT COUNT(ps.div_no) AS "main", COUNT(pasmater.pas_id) FROM mkadd.passport as ps
    #                 LEFT JOIN mkadd.passport_material_deviation as pasmater
    #                 ON pasmater.pas_id = ps.pas_id
    #                 WHERE ps.div_no = %s and ps.pas_date_del is null;""",
    #             [div],
    #         )
    #         result = cursor.fetchall()

    #         data.append(result[0][0])
    #         data1.append(result[0][1])
    context = {
        "div_no": div_no,
        "data": data,
        "data1": data1,
    }

    return render(request, "diplom/analytics.html", context=context)
