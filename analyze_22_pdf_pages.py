import os
from PyPDF2 import PdfReader

PDF_PATH = os.path.join(os.path.dirname(__file__), 'test-files', 'All_22_Paystubs.pdf')
PAGES_TO_CHECK = {2,3,12,15,21,46,48}

def main():
    if not os.path.exists(PDF_PATH):
        print('Missing PDF:', PDF_PATH)
        return
    reader = PdfReader(PDF_PATH)
    total = len(reader.pages)
    print(f'PDF pages: {total}')
    for p in sorted(PAGES_TO_CHECK):
        if p > total:
            print(f'-- Page {p} out of range')
            continue
        page = reader.pages[p-1]
        text = page.extract_text() or ''
        print('\n' + '='*80)
        print(f'PAGE {p} RAW (first 800 chars repr):')
        print(repr(text[:800]))
        print('\nSHAPE SUMMARY:')
        lines = text.splitlines()
        print(f' Lines: {len(lines)}  Non-empty: {sum(1 for l in lines if l.strip())}')
        # Show first 25 lines for structure
        for i, line in enumerate(lines[:25], start=1):
            print(f'{i:02d}: {line}')

if __name__ == '__main__':
    main()
