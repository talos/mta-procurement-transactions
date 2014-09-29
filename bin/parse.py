#!/usr/bin/env python


import sys
import csv
import re
import codecs


transaction_number = lambda s: re.search('^[0-9A-Za-z\-+.]+$', s) or s == u''
integer = lambda s: re.search(r'^\d+$', s) or s == u''
money = lambda s: re.search(r'^-?\$[0-9,]+\.?\d*$', s) or s in (u'', u'****************')
text = lambda s: True
date = lambda s: re.search(r'^\d{2}/\d{2}/\d{4}$', s) or s == u''
options = lambda *options: lambda s: s.lower() in [o.lower() for o in options]
yes_or_no = options('yes', 'no', '')

COLUMNS = dict((
    (u'page_number', integer),
    (u'vendor_number', integer),
    (u'vendor_name', text),
    (u'transaction_number', transaction_number),
    (u'procurement_description', text),
    (u'amount_expended_for_fiscal_year', money),
    (u'amount_expended_for_life_to_date', money),
    (u'does_the_contract_have_an_end_date', yes_or_no),
    (u'current_or_outstanding_balance', money),
    (u'number_of_bids_or_proposals_received_prior_to_award_of_contract', integer),
    (u'is_the_vendor_a_nys_or_foreign_business_enterprise?', options(u'foreign',
                                                                     u'nys',
                                                                     u'')),
    (u'is_the_vendor_a_minority_or_woman-owned_business_enterprise?', yes_or_no),
    (u'exemption_from_the_publication_requirements_of_article_4c_of_the_economic-development_law?', yes_or_no),
    (u'if_yes,_basis_for_exemption', text),
    (u'type_of_procurement', options(u'Staffing Services',
                                     u'Design and Construction/Maintenance',
                                     u'Commodities/Supplies',
                                     u'Consulting Services',
                                     u'Other',
                                     u'Technology - Hardware',
                                     u'Other Professional Services',
                                     u'Technology - Consulting/Development or Sup',
                                     u'Technology - Software',
                                     u'Legal Services',
                                     u'Telecommunication Equipment or Services',
                                     u'Financial Services')),
    (u'award_process', options(u'Authority Contract - Competitive Bid',
                               u'Non Contract Procurement/Purchase Order',
                               u'Purchased Under State Contract',
                               u'Authority Contract - Non-Competitive Bid')),
    (u'award_date', date),
    (u'begin_date', date),
    (u'renewal_date', date),
    (u'end_date', date),
    (u'amount', money),
    (u'fair_market_value', money),
    (u'explain_why_the_fair_market_value_is_less_than_the_contract_amount', text),
    (u'status', options('open', 'completed')),
    (u'were_mwbe_firms_solicited_as_part_of_this_procurement_proces', yes_or_no),
    (u'number_of_bids_and_proposal_received_from_mwbe_firms', integer),
    (u'address_line1', text),
    (u'address_line2', text),
    (u'city', text),
    (u'state', text),
    (u'postal_code', text),
    (u'plus_4', text),
    (u'province_region', text),
    (u'country', text)
))


def locate(pattern, page):
    for line in page.splitlines():
        match = re.search(pattern, page)
        if match:
            return match.span()
    raise Exception(u"Could not find {} in page '{}'".format(pattern, page))


def process_data(data):
    if re.search(r'^-?\$[\d,.]+$', data):
        return data.translate({ord('$'): None, ord(','): None})
    elif data == '****************': # Blacked out?  This messes with numbers.
        return ''
    return data


def parse(infile):

    reload(sys)
    sys.setdefaultencoding('utf-8')

    writer = csv.DictWriter(codecs.getwriter('utf8')(sys.stdout), COLUMNS.keys())
    pages = infile.read().split('Procurement Transactions Listing:')

    writer.writeheader()
    for i, page in enumerate(pages[2:]):
        page = page.decode('iso8859')

        output = {
            'page_number': i + 2,
        }

        lh, ld = locate(r'Vendor Name:\s+\S', page)
        rh, rd = locate(r'Type of Procurement:\s+\S', page)

        # Accumulators
        lha, lda, nlda, rha, rda, nrda = (u'', u'', u'', u'', u'', u'')

        _ = lambda x: x.strip().replace(' ', '_').lower()
        __ = lambda x, y: (_(x) + u'_' + _(y)).strip('_')

        for line in page.splitlines():
            if re.search(r'Page\s+\d+\s+of\s+\d+', line):
                # Clear out remaining data
                if lha:
                    output[_(lha)] = lda
                if rha:
                    output[_(rha)] = rda
                break

            vendor_number_match = re.search(r'^(\d+)\.?\s*Vendor Name:', line)
            if vendor_number_match:
                output[u'vendor_number'] = vendor_number_match.group(1)

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
                output[_(lha)] = process_data(lda)
                if not COLUMNS[_(lha)](lda):
                    raise Exception(u'Value "{}" invalid in column "{}"'.format(
                        lda, _(lha)))
                lha = u''
                lda = nlda
                nlda = u''

            if _(rha) in COLUMNS and not __(rha, right_header) in COLUMNS:
                output[_(rha)] = process_data(rda)
                if not COLUMNS[_(rha)](rda):
                    raise Exception(u'Value "{}" invalid in column "{}"'.format(
                        rda, _(rha)))
                rha = u''
                rda = nrda
                nrda = u''

            if left_header:
                lha = (lha + u' ' + left_header).strip(' ')

            if right_header:
                rha = (rha + u' ' + right_header).strip(' ')

            if left_data:
                if _(lha) in COLUMNS:
                    if COLUMNS[_(lha)]((lda + u' ' + left_data).strip(' ')):
                        lda = (lda + u' ' + left_data).strip(' ')
                    else:
                        nlda = (nlda + u' ' + left_data).strip(' ')
                else:
                    lda = (lda + u' ' + left_data).strip(' ')

            if right_data:
                if _(rha) in COLUMNS:
                    if COLUMNS[_(rha)]((rda + u' ' + right_data).strip(' ')):
                        rda = (rda + u' ' + right_data).strip(' ')
                    else:
                        nrda = (nrda + u' ' + right_data).strip(' ')
                else:
                    rda = (rda + u' ' + right_data).strip(' ')

        writer.writerow(output)


if __name__ == '__main__':
    parse(open(sys.argv[1], 'r'))
