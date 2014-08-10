#!/usr/bin/env python


import sys
import csv
import re


COLUMNS = (
    u'Run_Date',
    u'Fiscal_Year_Ending',
    u'Status',
    u'Vendor_Number',
    u'Vendor_Name',
    u'Transaction_Number',
    u'Procurement_Description',
    u'Amount_Expended_for_Fiscal_Year',
    u'Amount_Expended_for_Life_to_Date',
    u'Does_the_contract_have_an_end_date',
    u'Current_or_Outstanding_Balance',
    u'Number_Of_Bids_Or_Proposals_Received_Prior_to_Award_of_Contract',
    u'Is_the_Vendor_a_NYS_or_Foreign_Business_Enterprise',
    u'Is_the_Vendor_a_Minority_or_Woman-Owned_Business_Enterprise',
    u'Exemption_from_the_publication_requirements_of_Article_4c_of_the_economic-development_law?',
    u'If_Yes,_basis_for_exemption',
    u'Type_of_Procurement',
    u'Award_Process',
    u'Award_Date',
    u'Begin_Date',
    u'Renewal_Date',
    u'End_Date',
    u'Amount',
    u'Fair_Market_value',
    u'Explain_why_the_fair_market_value_is_less_than_the_contract_amount',
    u'Status',
    u'were_MWBE_firms_solicited_as_part_of_this_procurement_contract',
    u'Number_of_bids_and_proposals_received_from_MWBE_firms',
    u'Address_Line1',
    u'Address_Line2',
    u'City',
    u'State',
    u'Postal_Code',
    u'Plus_4',
    u'Province_Region',
    u'Country',
    u'Page'
)


WAITING = 'waiting'
LISTENING = 'listening'


def locate(pattern, page):
    for line in page.splitlines():
        match = re.search(pattern, page)
        if match:
            return match.span()
    raise Exception(u"Could not find {} in page '{}'".format(pattern, page))


def parse(infile):
    writer = csv.DictWriter(sys.stdout, COLUMNS)
    output = {}
    pages = infile.read().split('Procurement Transactions Listing:')

    writer.writeheader()
    for page in pages[2:]:
        page = page.decode('iso8859')

        lh, ld = locate(r'Vendor Name:\s+\S', page)
        rh, rd = locate(r'Type of Procurement:\s+\S', page)

        # Accumulators
        lha, lda, rha, rda = (u'', u'', u'', u'')

        _ = lambda x: x.replace(' ', '_').strip()
        __ = lambda x, y: _(x) + u'_' + _(y)

        for line in page.splitlines():
            left_header = line[lh-2:ld-3].strip().replace(':', '')
            left_data = line[ld-3:rh-2].strip()
            right_header = line[rh-2:rd-4].strip().replace(':', '')
            right_data = line[rd-4:].strip()

            if _(lha) in COLUMNS and not __(lha, left_header) in COLUMNS:
                output[_(lha)] = lda
                lha = u''
                lda = u''

            if _(rha) in COLUMNS and not __(rha, right_header) in COLUMNS:
                output[_(rha)] = rda
                rha = u''
                rda = u''

            if left_header:
                if lha:
                    lha += u' ' + left_header
                else:
                    lha = left_header

            if left_data:
                if lda:
                    lda += u' ' + left_data
                else:
                    lda = left_data

            if right_header:
                if rha:
                    rha += u' ' + right_header
                else:
                    rha = right_header

            if right_data:
                if rda:
                    rda += u' ' + right_data
                else:
                    rda = right_data

        writer.writerow(output)


if __name__ == '__main__':
    parse(open(sys.argv[1], 'r'))
