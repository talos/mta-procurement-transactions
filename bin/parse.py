#!/usr/bin/env python


import sys
import csv
import re
import codecs


COLUMNS = (
    u'number',
    u'vendor_number',
    u'vendor_name',
    u'transaction_number',
    u'procurement_description',
    u'amount_expended_for_fiscal_year',
    u'amount_expended_for_life_to_date',
    u'does_the_contract_have_an_end_date',
    u'current_or_outstanding_balance',
    u'number_of_bids_or_proposals_received_prior_to_award_of_contract',
    u'is_the_vendor_a_nys_or_foreign_business_enterprise?',
    u'is_the_vendor_a_minority_or_woman-owned_business_enterprise?',
    u'exemption_from_the_publication_requirements_of_article_4c_of_the_economic-development_law?',
    u'if_yes,_basis_for_exemption',
    u'type_of_procurement',
    u'award_process',
    u'award_date',
    u'begin_date',
    u'renewal_date',
    u'end_date',
    u'amount',
    u'fair_market_value',
    u'explain_why_the_fair_market_value_is_less_than_the_contract_amount',
    u'status',
    u'were_mwbe_firms_solicited_as_part_of_this_procurement_proces',
    u'number_of_bids_and_proposal_received_from_mwbe_firms',
    u'address_line1',
    u'address_line2',
    u'city',
    u'state',
    u'postal_code',
    u'plus_4',
    u'province_region',
    u'country'
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

    reload(sys)
    sys.setdefaultencoding('utf-8')

    writer = csv.DictWriter(codecs.getwriter('utf8')(sys.stdout), COLUMNS)
    output = {}
    pages = infile.read().split('Procurement Transactions Listing:')

    writer.writeheader()
    for page in pages[2:]:
        page = page.decode('iso8859')

        lh, ld = locate(r'Vendor Name:\s+\S', page)
        rh, rd = locate(r'Type of Procurement:\s+\S', page)

        # Accumulators
        lha, lda, rha, rda = (u'', u'', u'', u'')

        _ = lambda x: x.replace(' ', '_').strip().lower()
        __ = lambda x, y: _(x) + u'_' + _(y)

        for line in page.splitlines():
            if re.search(r'Page\s+\d+\s+of\s+\d+', line):
                # Clear out remaining data
                if lha:
                    output[_(lha)] = lda
                if rha:
                    output[_(rha)] = rda
                break

            if line[lh-3:lh-2] != '.':
                if re.search(r'\d', line[lh-3:lh-2]):
                    loffset = 2
                else:
                    loffset = 3
            else:
                loffset = 2

            left_header = line[lh-loffset:ld-3].strip().replace(':', '')
            left_data = line[ld-3:rh-2].strip('" ')
            right_header = line[rh-2:rd-4].strip().replace(':', '')
            right_data = line[rd-4:].strip('" ')

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
