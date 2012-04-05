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

__date__ = "2012 04 05"
__author__ = "tash"


import logging

from django.db import transaction

from ecm.apps.common.models import UpdateDate
from ecm.utils import tools
from ecm.apps.eve import api
from ecm.plugins.accounting.models import Contract

LOG = logging.getLogger(__name__)

#------------------------------------------------------------------------------
def update():
    """
    Update all contracts
    """
    LOG.info("fetching /corp/Contracts.xml.aspx...")
    # Connect to EVE API
    conn = api.connect()
    contracts_api = conn.corp.Contracts()
    api.check_version(contracts_api._meta.version)

    current_time = contracts_api._meta.currentTime
    cached_until = contracts_api._meta.cachedUntil
    LOG.debug("current time : %s", str(current_time))
    LOG.debug("cached util : %s", str(cached_until))
    LOG.debug("parsing api response...")

    # Get old contracts
    old_contracts = {}
    for contract in Contract.objects.all():
        old_contracts[contract] = contract

    # Get new contracts
    new_contracts = {}
    for row in contracts_api.contractList:
        contract = create_contract_fom_row(row)
        new_contracts[contract] = contract

    removed_contracts, added_contracts = tools.diff(old_contracts, new_contracts)
    write_results(added_contracts, removed_contracts)
    UpdateDate.mark_updated(model=Contract, date=current_time)

#------------------------------------------------------------------------------
@transaction.commit_on_success
def write_results(new_contracts, old_contracts):
    """
    Write the API results
    """
    if len(old_contracts) > 0:
        Contract.objects.all().delete()
        LOG.info("%d old contracts removed." % len(old_contracts))
    for contract in new_contracts:
        contract.save()
    LOG.info("%d contracts added." % len(new_contracts))

#------------------------------------------------------------------------------
def create_contract_fom_row(row):
    return Contract(contractID = row.contractID,
                    issuerID = row.issuerID,
                    issuerCorpID = row.issuerCorpID,
                    assigneeID = row.assigneeID,
                    acceptorID = row.acceptorID,
                    startStationID = row.startStationID,
                    endStationID = row.endStationID,
                    type = row.type,
                    status = row.status,
                    title = row.title,
                    forCorp = row.forCorp,
                    availability = row.availability,
                    dateIssued = row.dateIssued,
                    dateExpired = row.dateExpired,
                    dateAccepted = row.dateAccepted,
                    numDays = row.numDays,
                    dateCompleted = row.dateCompleted,
                    price = row.price,
                    reward = row.reward,
                    collateral = row.collateral,
                    buyout = row.buyout,
                    volume = row.volume)

