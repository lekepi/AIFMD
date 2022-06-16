from openpyxl import workbook, load_workbook

FILE_DIR = 'H:\Compliance\AIFMD\KEY FILES\AIFMD Manual Data.xlsm'


wb = load_workbook(FILE_DIR)
ws = wb.active
EURUSD_RATE = ws['B5'].value

# Q4 2021:
# EURUSD_RATE = 1.1326  # 31/12/2021 on the ecb website
# https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/eurofxref-graph-usd.en.html

# 48
AUM_ALTO_USD = round(ws['B8'].value, 0)  # From Dorothée?
AUM_NEUTRAL_USD = round(ws['C8'].value, 0)  # From Dorothée?

# 53
NAV_ALTO_USD = round(ws['B9'].value, 0)
NAV_NEUTRAL_USD = round(ws['C9'].value, 0)

# 118
MainBeneficialOwnersRate_alto = round(ws['B10'].value*100, 2)  # Beneficially owned percentage by top 5 beneficial owners
MainBeneficialOwnersRate_neutral = round(ws['C10'].value*100, 2)  # Beneficially owned percentage by top 5 beneficial owners

# 137
AnnualInvestmentReturnRate_alto = round(ws['B11'].value*100, 2)   # Expected annual investment return in %
AnnualInvestmentReturnRate_neutral = round(ws['C11'].value*100, 2)   # Expected annual investment return in %

# 157
AllCounterpartyCollateralCash_alto = round(ws['B12'].value, 0)
AllCounterpartyCollateralCash_neutral = round(ws['C12'].value, 0)

# 185
UnencumberedCash_alto = round(ws['B13'].value, 0)
UnencumberedCash_neutral = round(ws['C13'].value, 0)

# 219-230 Gross investment return in % for the 3 month of the quarter (2 decimals)
GrossInvestmentReturnsRate_alto = [round(ws['B16'].value, 2), round(ws['C16'].value, 2), round(ws['D16'].value, 2)]
GrossInvestmentReturnsRate_neutral = [round(ws['B23'].value, 2), round(ws['C23'].value, 2), round(ws['D23'].value, 2)]

# 231-242 Percentage of net investment returns in % for the 3 month of the quarter (2 decimals)
NetInvestmentReturnsRate_alto = [round(ws['B17'].value, 2), round(ws['C17'].value, 2), round(ws['D17'].value, 2)]
NetInvestmentReturnsRate_neutral = [round(ws['B24'].value, 2), round(ws['C24'].value, 2), round(ws['D24'].value, 2)]

# 243-254 NAV change in % for the 3 month of the quarter (2 decimals)
NAVChangeRate_alto = [round(ws['B18'].value, 2), round(ws['C18'].value, 2), round(ws['D18'].value, 2)]
NAVChangeRate_neutral = [round(ws['B25'].value, 2), round(ws['C25'].value, 2), round(ws['D25'].value, 2)]

# 255-266 Subscription amount in $ for the 3 month of the quarter (0 decimals)
Subscription_alto = [round(ws['B19'].value, 0), round(ws['C19'].value, 0), round(ws['D19'].value, 0)]
Subscription_neutral = [round(ws['B26'].value, 0), round(ws['C26'].value, 0), round(ws['D26'].value, 0)]

# 267-278 Redemption amount in $ for the 3 month of the quarter (0 decimals)
Redemption_alto = [round(ws['B20'].value, 0), round(ws['C20'].value, 0), round(ws['D20'].value, 0)]
Redemption_neutral = [round(ws['B27'].value, 0), round(ws['C27'].value, 0), round(ws['D27'].value, 0)]

# 279 Results of stress tests performed in accordance with point(b) of Article 15(3)
StressTestsResultArticle15_alto = ws['B30'].value
StressTestsResultArticle15_neutral = ws['H30'].value

# 280 Results of stress tests performed in accordance with the second subparagraph of Article 16(1)
StressTestsResultArticle16_alto = ws['B31'].value
StressTestsResultArticle16_neutral = ws['H31'].value

# 287 Exchange traded derivatives exposure amount
ExchangedTradedDerivativesExposureValue_alto = round(ws['B34'].value, 0)
ExchangedTradedDerivativesExposureValue_neutral = round(ws['C34'].value, 0)

# 288 OTC derivatives exposure amount
OTCDerivativesAmount_alto = round(ws['B35'].value, 0)
OTCDerivativesAmount_neutral = round(ws['C35'].value, 0)

# 289 - Short position borrowed securities value
ShortPositionBorrowedSecuritiesValue_alto = round(ws['B36'].value, 0)
ShortPositionBorrowedSecuritiesValue_neutral = round(ws['C36'].value, 0)

# 294 - Leverage under gross method
GrossMethodRate_alto = round(ws['B37'].value, 2)
GrossMethodRate_neutral = round(ws['C37'].value, 2)

# 295 - Leverage under commitment method
CommitmentMethodRate_alto = round(ws['B38'].value, 2)
CommitmentMethodRate_neutral = round(ws['C38'].value, 2)

# 301 - Received leverage amount
LeverageAmount_GS = round(ws['B41'].value, 0)
LeverageAmount_MS = round(ws['C41'].value, 0)
LeverageAmount_UBS = round(ws['D41'].value, 0)








