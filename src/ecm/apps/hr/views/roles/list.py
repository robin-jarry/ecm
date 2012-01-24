# Copyright (c) 2010-2012 Robin Jarry
#
# This file is part of EVE Corporation Management.
#
# EVE Corporation Management is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# EVE Corporation Management is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# EVE Corporation Management. If not, see <http://www.gnu.org/licenses/>.

__date__ = "2011-03-02"
__author__ = "diabeteman"

try:
    import json
except ImportError:
    # fallback for python 2.5
    import django.utils.simplejson as json
import httplib as http

from django.shortcuts import render_to_response, redirect
from django.views.decorators.cache import cache_page
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest, Http404
from django.template.context import RequestContext as Ctx

from ecm.apps.hr import NAME as app_prefix
from ecm.apps.hr.models import Role, RoleType
from ecm.apps.common.models import ColorThreshold
from ecm.views.decorators import check_user_access
from ecm.apps.corp.models import Hangar, Wallet

import logging
logger = logging.getLogger(__name__)

#------------------------------------------------------------------------------
def root(request):
    return redirect("/%s/roles/roles/" % app_prefix)

#------------------------------------------------------------------------------
@check_user_access()
def role_type(request, role_typeName):
    try:
        role_type = RoleType.objects.get(typeName=role_typeName)
    except ObjectDoesNotExist:
        raise Http404()

    data = {
        'colorThresholds' : ColorThreshold.as_json(),
        'role_types' : RoleType.objects.all().order_by('id'),
        'current_role_type' : role_type.typeName,
        'current_role_type_name' : role_type.dispName,
    }
    return render_to_response("roles/roles.html", data, Ctx(request))



#------------------------------------------------------------------------------
@check_user_access()
@cache_page(3 * 60 * 60) # 3 hours cache
def role_type_data(request, role_typeName):
    try:
        role_type = RoleType.objects.get(typeName=role_typeName)
        sEcho = int(request.REQUEST["sEcho"])
    except ObjectDoesNotExist:
        return HttpResponseNotFound()
    except KeyError:
        return HttpResponseBadRequest()

    roles = []
    for role in Role.objects.filter(roleType=role_type).order_by("roleID"):

        members = role.members.all()
        if members.count():
            members = list(members)
            members.sort()
            members = [m.name for m in members]
            members.insert(0, "Members")

        titles = list(role.titles.values_list("titleName", flat=True))
        if titles:
            titles.insert(0, "Titles")

        roles.append([
            role.permalink,
            role.description,
            role.get_access_lvl(),
            role.members.count(),
            role.titles.count(),
            role.id,
            "|".join(members),
            "|".join(titles)
        ])

    json_data = {
        "sEcho" : sEcho,
        "iTotalRecords" : len(roles),
        "iTotalDisplayRecords" : len(roles),
        "aaData" : roles
    }

    return HttpResponse(json.dumps(json_data))

#------------------------------------------------------------------------------
@check_user_access()
def update_access_level(request):
    try:
        role_id = int(request.POST["id"])
        new_access_level = int(request.POST["value"])
        role = Role.objects.get(id=role_id)

        if role.hangar_id:
            # Here, the access level is related to a hangar division
            # we must modify the access level of the related hangar
            #
            # note: this will propagate the change of access level
            #       through all roles that depend on that hangar division
            Hangar.objects.filter(hangarID=role.hangar_id).update(accessLvl=new_access_level)

        elif role.wallet_id:
            # Same as above, but with wallet divisions
            Wallet.objects.filter(walletID=role.wallet_id).update(accessLvl=new_access_level)

        elif role.roleID == 1:
            # the "director" role is specific, it is redundant in 4 role categories
            # we modify the access level of all 4 instances of the role at once
            Role.objects.filter(roleID=1).update(accessLvl=new_access_level)

        else:
            role.accessLvl = new_access_level
            role.save()
        logger.info('"%s" changed access level for role "%s" -> %d' % (request.user, role, new_access_level))
        return HttpResponse(content=str(new_access_level), status=http.ACCEPTED)
    except:
        return HttpResponseBadRequest()



