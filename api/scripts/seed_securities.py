"""
Seed script for common securities.

Pre-populates the security registry with:
- Major ETFs (SPY, QQQ, IWM, VTI, etc.)
- Sample Treasury bonds for learning
- Some blue-chip stocks

Usage:
    cd api
    poetry run python scripts/seed_securities.py
"""

import os
import sys
from datetime import date
from decimal import Decimal
from uuid import uuid4

import psycopg2
from psycopg2.extras import execute_values

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dependencies import load_config


# =============================================================================
# SEED DATA DEFINITIONS
# =============================================================================

ETFS = [
    # ==========================================================================
    # BROAD MARKET
    # ==========================================================================
    ("SPY", "SPDR S&P 500 ETF Trust", "Broad Market", "NYSE"),
    ("QQQ", "Invesco QQQ Trust", "Technology", "NASDAQ"),
    ("IWM", "iShares Russell 2000 ETF", "Small Cap", "NYSE"),
    ("VTI", "Vanguard Total Stock Market ETF", "Broad Market", "NYSE"),
    ("VOO", "Vanguard S&P 500 ETF", "Broad Market", "NYSE"),
    ("DIA", "SPDR Dow Jones Industrial Average ETF", "Broad Market", "NYSE"),
    ("MDY", "SPDR S&P MidCap 400 ETF", "Mid Cap", "NYSE"),
    ("IJH", "iShares Core S&P Mid-Cap ETF", "Mid Cap", "NYSE"),
    ("IJR", "iShares Core S&P Small-Cap ETF", "Small Cap", "NYSE"),
    # ==========================================================================
    # SECTOR ETFS (Complete SPDR Sector Suite)
    # ==========================================================================
    ("XLB", "Materials Select Sector SPDR Fund", "Materials", "NYSE"),
    ("XLC", "Communication Services Select Sector SPDR", "Communication Services", "NYSE"),
    ("XLE", "Energy Select Sector SPDR Fund", "Energy", "NYSE"),
    ("XLF", "Financial Select Sector SPDR Fund", "Financials", "NYSE"),
    ("XLI", "Industrial Select Sector SPDR Fund", "Industrials", "NYSE"),
    ("XLK", "Technology Select Sector SPDR Fund", "Technology", "NYSE"),
    ("XLP", "Consumer Staples Select Sector SPDR Fund", "Consumer Staples", "NYSE"),
    ("XLRE", "Real Estate Select Sector SPDR Fund", "Real Estate", "NYSE"),
    ("XLU", "Utilities Select Sector SPDR Fund", "Utilities", "NYSE"),
    ("XLV", "Health Care Select Sector SPDR Fund", "Healthcare", "NYSE"),
    ("XLY", "Consumer Discretionary Select Sector SPDR", "Consumer Discretionary", "NYSE"),
    # ==========================================================================
    # FACTOR/STYLE ETFS
    # ==========================================================================
    ("VTV", "Vanguard Value ETF", "Value", "NYSE"),
    ("VUG", "Vanguard Growth ETF", "Growth", "NYSE"),
    ("MTUM", "iShares MSCI USA Momentum Factor ETF", "Momentum", "NYSE"),
    ("QUAL", "iShares MSCI USA Quality Factor ETF", "Quality", "NYSE"),
    ("USMV", "iShares MSCI USA Min Vol Factor ETF", "Low Volatility", "NYSE"),
    ("VLUE", "iShares MSCI USA Value Factor ETF", "Value", "NYSE"),
    ("SIZE", "iShares MSCI USA Size Factor ETF", "Size", "NYSE"),
    ("DGRO", "iShares Core Dividend Growth ETF", "Dividend Growth", "NYSE"),
    ("VIG", "Vanguard Dividend Appreciation ETF", "Dividend Growth", "NYSE"),
    ("SCHD", "Schwab US Dividend Equity ETF", "Dividend", "NYSE"),
    ("HDV", "iShares Core High Dividend ETF", "High Dividend", "NYSE"),
    # ==========================================================================
    # INTERNATIONAL DEVELOPED
    # ==========================================================================
    ("VEA", "Vanguard FTSE Developed Markets ETF", "International Developed", "NYSE"),
    ("EFA", "iShares MSCI EAFE ETF", "International Developed", "NYSE"),
    ("IEFA", "iShares Core MSCI EAFE ETF", "International Developed", "NYSE"),
    ("EWJ", "iShares MSCI Japan ETF", "Japan", "NYSE"),
    ("EWG", "iShares MSCI Germany ETF", "Germany", "NYSE"),
    ("EWU", "iShares MSCI United Kingdom ETF", "United Kingdom", "NYSE"),
    ("EWC", "iShares MSCI Canada ETF", "Canada", "NYSE"),
    ("EWA", "iShares MSCI Australia ETF", "Australia", "NYSE"),
    # ==========================================================================
    # EMERGING MARKETS
    # ==========================================================================
    ("VWO", "Vanguard FTSE Emerging Markets ETF", "Emerging Markets", "NYSE"),
    ("EEM", "iShares MSCI Emerging Markets ETF", "Emerging Markets", "NYSE"),
    ("IEMG", "iShares Core MSCI Emerging Markets ETF", "Emerging Markets", "NYSE"),
    ("FXI", "iShares China Large-Cap ETF", "China", "NYSE"),
    ("EWZ", "iShares MSCI Brazil ETF", "Brazil", "NYSE"),
    ("INDA", "iShares MSCI India ETF", "India", "NYSE"),
    ("EWT", "iShares MSCI Taiwan ETF", "Taiwan", "NYSE"),
    ("EWY", "iShares MSCI South Korea ETF", "South Korea", "NYSE"),
    # ==========================================================================
    # FIXED INCOME - GOVERNMENT
    # ==========================================================================
    ("BND", "Vanguard Total Bond Market ETF", "Fixed Income", "NYSE"),
    ("AGG", "iShares Core US Aggregate Bond ETF", "Fixed Income", "NYSE"),
    ("TLT", "iShares 20+ Year Treasury Bond ETF", "Long-Term Treasury", "NYSE"),
    ("IEF", "iShares 7-10 Year Treasury Bond ETF", "Intermediate Treasury", "NYSE"),
    ("SHY", "iShares 1-3 Year Treasury Bond ETF", "Short-Term Treasury", "NYSE"),
    ("TIP", "iShares TIPS Bond ETF", "Inflation Protected", "NYSE"),
    ("GOVT", "iShares US Treasury Bond ETF", "Treasury", "NYSE"),
    # ==========================================================================
    # FIXED INCOME - CORPORATE & OTHER
    # ==========================================================================
    ("LQD", "iShares iBoxx Investment Grade Corp Bond ETF", "Investment Grade Corp", "NYSE"),
    ("HYG", "iShares iBoxx High Yield Corporate Bond ETF", "High Yield Corp", "NYSE"),
    ("JNK", "SPDR Bloomberg High Yield Bond ETF", "High Yield Corp", "NYSE"),
    ("MUB", "iShares National Muni Bond ETF", "Municipal Bonds", "NYSE"),
    ("EMB", "iShares JP Morgan USD Emerging Markets Bond ETF", "EM Bonds", "NYSE"),
    ("BNDX", "Vanguard Total International Bond ETF", "International Bonds", "NYSE"),
    # ==========================================================================
    # COMMODITIES & ALTERNATIVES
    # ==========================================================================
    ("GLD", "SPDR Gold Shares", "Gold", "NYSE"),
    ("IAU", "iShares Gold Trust", "Gold", "NYSE"),
    ("SLV", "iShares Silver Trust", "Silver", "NYSE"),
    ("USO", "United States Oil Fund", "Crude Oil", "NYSE"),
    ("DBC", "Invesco DB Commodity Index Tracking Fund", "Broad Commodities", "NYSE"),
    ("GSG", "iShares S&P GSCI Commodity-Indexed Trust", "Broad Commodities", "NYSE"),
    # ==========================================================================
    # REAL ESTATE
    # ==========================================================================
    ("VNQ", "Vanguard Real Estate ETF", "Real Estate", "NYSE"),
    ("IYR", "iShares US Real Estate ETF", "Real Estate", "NYSE"),
    ("VNQI", "Vanguard Global ex-US Real Estate ETF", "International Real Estate", "NYSE"),
    # ==========================================================================
    # THEMATIC - TECHNOLOGY & INNOVATION
    # ==========================================================================
    ("ARKK", "ARK Innovation ETF", "Innovation", "NYSE"),
    ("SOXX", "iShares Semiconductor ETF", "Semiconductors", "NYSE"),
    ("SMH", "VanEck Semiconductor ETF", "Semiconductors", "NYSE"),
    ("SKYY", "First Trust Cloud Computing ETF", "Cloud Computing", "NYSE"),
    ("BOTZ", "Global X Robotics & AI ETF", "Robotics & AI", "NYSE"),
    ("HACK", "ETFMG Prime Cyber Security ETF", "Cybersecurity", "NYSE"),
    ("FINX", "Global X FinTech ETF", "FinTech", "NYSE"),
    # ==========================================================================
    # THEMATIC - CLEAN ENERGY & ESG
    # ==========================================================================
    ("ICLN", "iShares Global Clean Energy ETF", "Clean Energy", "NYSE"),
    ("TAN", "Invesco Solar ETF", "Solar Energy", "NYSE"),
    ("QCLN", "First Trust NASDAQ Clean Edge Green Energy", "Clean Energy", "NYSE"),
    ("PBW", "Invesco WilderHill Clean Energy ETF", "Clean Energy", "NYSE"),
    ("LIT", "Global X Lithium & Battery Tech ETF", "Lithium & Batteries", "NYSE"),
    # ==========================================================================
    # THEMATIC - INFRASTRUCTURE & DEFENSE
    # ==========================================================================
    ("PAVE", "Global X US Infrastructure Development ETF", "Infrastructure", "NYSE"),
    ("ITA", "iShares US Aerospace & Defense ETF", "Aerospace & Defense", "NYSE"),
    ("XAR", "SPDR S&P Aerospace & Defense ETF", "Aerospace & Defense", "NYSE"),
    # ==========================================================================
    # THEMATIC - HEALTHCARE & BIOTECH
    # ==========================================================================
    ("IBB", "iShares Biotechnology ETF", "Biotechnology", "NYSE"),
    ("XBI", "SPDR S&P Biotech ETF", "Biotechnology", "NYSE"),
    ("IHI", "iShares US Medical Devices ETF", "Medical Devices", "NYSE"),
]

STOCKS = [
    # ==========================================================================
    # TECHNOLOGY - MEGA CAP
    # ==========================================================================
    ("AAPL", "Apple Inc.", "Technology", "Consumer Electronics", "NASDAQ"),
    ("MSFT", "Microsoft Corporation", "Technology", "Software", "NASDAQ"),
    ("GOOGL", "Alphabet Inc.", "Communication Services", "Internet Services", "NASDAQ"),
    ("AMZN", "Amazon.com Inc.", "Consumer Discretionary", "E-Commerce", "NASDAQ"),
    ("NVDA", "NVIDIA Corporation", "Technology", "Semiconductors", "NASDAQ"),
    ("META", "Meta Platforms Inc.", "Communication Services", "Social Media", "NASDAQ"),
    ("TSLA", "Tesla Inc.", "Consumer Discretionary", "Automobiles", "NASDAQ"),
    # ==========================================================================
    # TECHNOLOGY - SEMICONDUCTORS
    # ==========================================================================
    ("AMD", "Advanced Micro Devices Inc.", "Technology", "Semiconductors", "NASDAQ"),
    ("INTC", "Intel Corporation", "Technology", "Semiconductors", "NASDAQ"),
    ("AVGO", "Broadcom Inc.", "Technology", "Semiconductors", "NASDAQ"),
    ("QCOM", "Qualcomm Inc.", "Technology", "Semiconductors", "NASDAQ"),
    ("TXN", "Texas Instruments Inc.", "Technology", "Semiconductors", "NASDAQ"),
    ("MU", "Micron Technology Inc.", "Technology", "Semiconductors", "NASDAQ"),
    ("AMAT", "Applied Materials Inc.", "Technology", "Semiconductor Equipment", "NASDAQ"),
    ("LRCX", "Lam Research Corporation", "Technology", "Semiconductor Equipment", "NASDAQ"),
    ("ASML", "ASML Holding N.V.", "Technology", "Semiconductor Equipment", "NASDAQ"),
    # ==========================================================================
    # TECHNOLOGY - SOFTWARE & CLOUD
    # ==========================================================================
    ("CRM", "Salesforce Inc.", "Technology", "Software", "NYSE"),
    ("ORCL", "Oracle Corporation", "Technology", "Software", "NYSE"),
    ("ADBE", "Adobe Inc.", "Technology", "Software", "NASDAQ"),
    ("NOW", "ServiceNow Inc.", "Technology", "Software", "NYSE"),
    ("INTU", "Intuit Inc.", "Technology", "Software", "NASDAQ"),
    ("SNOW", "Snowflake Inc.", "Technology", "Cloud Computing", "NYSE"),
    ("PANW", "Palo Alto Networks Inc.", "Technology", "Cybersecurity", "NASDAQ"),
    ("CRWD", "CrowdStrike Holdings Inc.", "Technology", "Cybersecurity", "NASDAQ"),
    # ==========================================================================
    # FINANCIALS - BANKS
    # ==========================================================================
    ("JPM", "JPMorgan Chase & Co.", "Financials", "Banking", "NYSE"),
    ("BAC", "Bank of America Corporation", "Financials", "Banking", "NYSE"),
    ("WFC", "Wells Fargo & Company", "Financials", "Banking", "NYSE"),
    ("C", "Citigroup Inc.", "Financials", "Banking", "NYSE"),
    ("GS", "Goldman Sachs Group Inc.", "Financials", "Investment Banking", "NYSE"),
    ("MS", "Morgan Stanley", "Financials", "Investment Banking", "NYSE"),
    ("USB", "U.S. Bancorp", "Financials", "Regional Banking", "NYSE"),
    ("PNC", "PNC Financial Services Group", "Financials", "Regional Banking", "NYSE"),
    # ==========================================================================
    # FINANCIALS - DIVERSIFIED
    # ==========================================================================
    ("V", "Visa Inc.", "Financials", "Payment Processing", "NYSE"),
    ("MA", "Mastercard Inc.", "Financials", "Payment Processing", "NYSE"),
    ("AXP", "American Express Company", "Financials", "Consumer Finance", "NYSE"),
    ("BLK", "BlackRock Inc.", "Financials", "Asset Management", "NYSE"),
    ("SCHW", "Charles Schwab Corporation", "Financials", "Brokerage", "NYSE"),
    ("BRK-B", "Berkshire Hathaway Inc.", "Financials", "Diversified", "NYSE"),
    # ==========================================================================
    # FINANCIALS - INSURANCE
    # ==========================================================================
    ("PGR", "Progressive Corporation", "Financials", "Insurance", "NYSE"),
    ("TRV", "Travelers Companies Inc.", "Financials", "Insurance", "NYSE"),
    ("MET", "MetLife Inc.", "Financials", "Insurance", "NYSE"),
    ("AIG", "American International Group", "Financials", "Insurance", "NYSE"),
    # ==========================================================================
    # HEALTHCARE - PHARMA & BIOTECH
    # ==========================================================================
    ("JNJ", "Johnson & Johnson", "Healthcare", "Pharmaceuticals", "NYSE"),
    ("UNH", "UnitedHealth Group Inc.", "Healthcare", "Health Insurance", "NYSE"),
    ("PFE", "Pfizer Inc.", "Healthcare", "Pharmaceuticals", "NYSE"),
    ("ABBV", "AbbVie Inc.", "Healthcare", "Pharmaceuticals", "NYSE"),
    ("MRK", "Merck & Co. Inc.", "Healthcare", "Pharmaceuticals", "NYSE"),
    ("LLY", "Eli Lilly and Company", "Healthcare", "Pharmaceuticals", "NYSE"),
    ("BMY", "Bristol-Myers Squibb Company", "Healthcare", "Pharmaceuticals", "NYSE"),
    ("AMGN", "Amgen Inc.", "Healthcare", "Biotechnology", "NASDAQ"),
    ("GILD", "Gilead Sciences Inc.", "Healthcare", "Biotechnology", "NASDAQ"),
    ("REGN", "Regeneron Pharmaceuticals Inc.", "Healthcare", "Biotechnology", "NASDAQ"),
    ("VRTX", "Vertex Pharmaceuticals Inc.", "Healthcare", "Biotechnology", "NASDAQ"),
    ("MRNA", "Moderna Inc.", "Healthcare", "Biotechnology", "NASDAQ"),
    # ==========================================================================
    # HEALTHCARE - DEVICES & SERVICES
    # ==========================================================================
    ("TMO", "Thermo Fisher Scientific Inc.", "Healthcare", "Life Sciences", "NYSE"),
    ("DHR", "Danaher Corporation", "Healthcare", "Life Sciences", "NYSE"),
    ("ABT", "Abbott Laboratories", "Healthcare", "Medical Devices", "NYSE"),
    ("MDT", "Medtronic plc", "Healthcare", "Medical Devices", "NYSE"),
    ("ISRG", "Intuitive Surgical Inc.", "Healthcare", "Medical Devices", "NASDAQ"),
    ("CVS", "CVS Health Corporation", "Healthcare", "Healthcare Services", "NYSE"),
    ("CI", "Cigna Group", "Healthcare", "Health Insurance", "NYSE"),
    ("ELV", "Elevance Health Inc.", "Healthcare", "Health Insurance", "NYSE"),
    ("HCA", "HCA Healthcare Inc.", "Healthcare", "Healthcare Facilities", "NYSE"),
    # ==========================================================================
    # CONSUMER STAPLES - DEFENSIVE
    # ==========================================================================
    ("WMT", "Walmart Inc.", "Consumer Staples", "Retail", "NYSE"),
    ("PG", "Procter & Gamble Co.", "Consumer Staples", "Household Products", "NYSE"),
    ("KO", "Coca-Cola Company", "Consumer Staples", "Beverages", "NYSE"),
    ("PEP", "PepsiCo Inc.", "Consumer Staples", "Beverages", "NASDAQ"),
    ("COST", "Costco Wholesale Corporation", "Consumer Staples", "Retail", "NASDAQ"),
    ("PM", "Philip Morris International", "Consumer Staples", "Tobacco", "NYSE"),
    ("MO", "Altria Group Inc.", "Consumer Staples", "Tobacco", "NYSE"),
    ("CL", "Colgate-Palmolive Company", "Consumer Staples", "Household Products", "NYSE"),
    ("KMB", "Kimberly-Clark Corporation", "Consumer Staples", "Household Products", "NYSE"),
    ("GIS", "General Mills Inc.", "Consumer Staples", "Food Products", "NYSE"),
    ("K", "Kellanova", "Consumer Staples", "Food Products", "NYSE"),
    ("KHC", "Kraft Heinz Company", "Consumer Staples", "Food Products", "NASDAQ"),
    ("MDLZ", "Mondelez International Inc.", "Consumer Staples", "Food Products", "NASDAQ"),
    ("STZ", "Constellation Brands Inc.", "Consumer Staples", "Alcoholic Beverages", "NYSE"),
    # ==========================================================================
    # CONSUMER DISCRETIONARY - CYCLICAL
    # ==========================================================================
    ("HD", "The Home Depot Inc.", "Consumer Discretionary", "Home Improvement", "NYSE"),
    ("LOW", "Lowe's Companies Inc.", "Consumer Discretionary", "Home Improvement", "NYSE"),
    ("MCD", "McDonald's Corporation", "Consumer Discretionary", "Restaurants", "NYSE"),
    ("SBUX", "Starbucks Corporation", "Consumer Discretionary", "Restaurants", "NASDAQ"),
    ("NKE", "Nike Inc.", "Consumer Discretionary", "Apparel", "NYSE"),
    ("TGT", "Target Corporation", "Consumer Discretionary", "Retail", "NYSE"),
    ("TJX", "TJX Companies Inc.", "Consumer Discretionary", "Retail", "NYSE"),
    ("BKNG", "Booking Holdings Inc.", "Consumer Discretionary", "Travel", "NASDAQ"),
    ("MAR", "Marriott International Inc.", "Consumer Discretionary", "Hotels", "NASDAQ"),
    ("DIS", "Walt Disney Company", "Communication Services", "Entertainment", "NYSE"),
    ("NFLX", "Netflix Inc.", "Communication Services", "Streaming", "NASDAQ"),
    ("F", "Ford Motor Company", "Consumer Discretionary", "Automobiles", "NYSE"),
    ("GM", "General Motors Company", "Consumer Discretionary", "Automobiles", "NYSE"),
    # ==========================================================================
    # ENERGY - OIL & GAS
    # ==========================================================================
    ("XOM", "Exxon Mobil Corporation", "Energy", "Oil & Gas Integrated", "NYSE"),
    ("CVX", "Chevron Corporation", "Energy", "Oil & Gas Integrated", "NYSE"),
    ("COP", "ConocoPhillips", "Energy", "Oil & Gas E&P", "NYSE"),
    ("EOG", "EOG Resources Inc.", "Energy", "Oil & Gas E&P", "NYSE"),
    ("SLB", "Schlumberger Limited", "Energy", "Oil Services", "NYSE"),
    ("OXY", "Occidental Petroleum Corporation", "Energy", "Oil & Gas E&P", "NYSE"),
    ("MPC", "Marathon Petroleum Corporation", "Energy", "Oil Refining", "NYSE"),
    ("PSX", "Phillips 66", "Energy", "Oil Refining", "NYSE"),
    ("VLO", "Valero Energy Corporation", "Energy", "Oil Refining", "NYSE"),
    ("HAL", "Halliburton Company", "Energy", "Oil Services", "NYSE"),
    # ==========================================================================
    # INDUSTRIALS - DIVERSIFIED
    # ==========================================================================
    ("CAT", "Caterpillar Inc.", "Industrials", "Machinery", "NYSE"),
    ("DE", "Deere & Company", "Industrials", "Machinery", "NYSE"),
    ("HON", "Honeywell International Inc.", "Industrials", "Diversified", "NASDAQ"),
    ("UNP", "Union Pacific Corporation", "Industrials", "Railroads", "NYSE"),
    ("UPS", "United Parcel Service Inc.", "Industrials", "Logistics", "NYSE"),
    ("FDX", "FedEx Corporation", "Industrials", "Logistics", "NYSE"),
    ("BA", "Boeing Company", "Industrials", "Aerospace", "NYSE"),
    ("RTX", "RTX Corporation", "Industrials", "Aerospace & Defense", "NYSE"),
    ("LMT", "Lockheed Martin Corporation", "Industrials", "Aerospace & Defense", "NYSE"),
    ("NOC", "Northrop Grumman Corporation", "Industrials", "Aerospace & Defense", "NYSE"),
    ("GD", "General Dynamics Corporation", "Industrials", "Aerospace & Defense", "NYSE"),
    ("GE", "GE Aerospace", "Industrials", "Aerospace", "NYSE"),
    ("MMM", "3M Company", "Industrials", "Diversified", "NYSE"),
    ("EMR", "Emerson Electric Co.", "Industrials", "Electrical Equipment", "NYSE"),
    ("ETN", "Eaton Corporation", "Industrials", "Electrical Equipment", "NYSE"),
    ("WM", "Waste Management Inc.", "Industrials", "Waste Management", "NYSE"),
    # ==========================================================================
    # MATERIALS
    # ==========================================================================
    ("LIN", "Linde plc", "Materials", "Industrial Gases", "NYSE"),
    ("APD", "Air Products and Chemicals", "Materials", "Industrial Gases", "NYSE"),
    ("SHW", "Sherwin-Williams Company", "Materials", "Specialty Chemicals", "NYSE"),
    ("FCX", "Freeport-McMoRan Inc.", "Materials", "Copper Mining", "NYSE"),
    ("NEM", "Newmont Corporation", "Materials", "Gold Mining", "NYSE"),
    ("NUE", "Nucor Corporation", "Materials", "Steel", "NYSE"),
    ("DD", "DuPont de Nemours Inc.", "Materials", "Specialty Chemicals", "NYSE"),
    ("DOW", "Dow Inc.", "Materials", "Chemicals", "NYSE"),
    # ==========================================================================
    # UTILITIES - DEFENSIVE / RATE SENSITIVE
    # ==========================================================================
    ("NEE", "NextEra Energy Inc.", "Utilities", "Electric Utilities", "NYSE"),
    ("DUK", "Duke Energy Corporation", "Utilities", "Electric Utilities", "NYSE"),
    ("SO", "Southern Company", "Utilities", "Electric Utilities", "NYSE"),
    ("D", "Dominion Energy Inc.", "Utilities", "Electric Utilities", "NYSE"),
    ("AEP", "American Electric Power", "Utilities", "Electric Utilities", "NASDAQ"),
    ("EXC", "Exelon Corporation", "Utilities", "Electric Utilities", "NASDAQ"),
    ("SRE", "Sempra", "Utilities", "Multi-Utilities", "NYSE"),
    ("XEL", "Xcel Energy Inc.", "Utilities", "Electric Utilities", "NASDAQ"),
    # ==========================================================================
    # REAL ESTATE - RATE SENSITIVE
    # ==========================================================================
    ("PLD", "Prologis Inc.", "Real Estate", "Industrial REIT", "NYSE"),
    ("AMT", "American Tower Corporation", "Real Estate", "Tower REIT", "NYSE"),
    ("CCI", "Crown Castle Inc.", "Real Estate", "Tower REIT", "NYSE"),
    ("EQIX", "Equinix Inc.", "Real Estate", "Data Center REIT", "NASDAQ"),
    ("SPG", "Simon Property Group", "Real Estate", "Retail REIT", "NYSE"),
    ("O", "Realty Income Corporation", "Real Estate", "Net Lease REIT", "NYSE"),
    ("PSA", "Public Storage", "Real Estate", "Self-Storage REIT", "NYSE"),
    ("WELL", "Welltower Inc.", "Real Estate", "Healthcare REIT", "NYSE"),
    ("AVB", "AvalonBay Communities Inc.", "Real Estate", "Residential REIT", "NYSE"),
    ("DLR", "Digital Realty Trust Inc.", "Real Estate", "Data Center REIT", "NYSE"),
    # ==========================================================================
    # COMMUNICATION SERVICES
    # ==========================================================================
    ("T", "AT&T Inc.", "Communication Services", "Telecom", "NYSE"),
    ("VZ", "Verizon Communications Inc.", "Communication Services", "Telecom", "NYSE"),
    ("TMUS", "T-Mobile US Inc.", "Communication Services", "Telecom", "NASDAQ"),
    ("CMCSA", "Comcast Corporation", "Communication Services", "Cable", "NASDAQ"),
    ("CHTR", "Charter Communications Inc.", "Communication Services", "Cable", "NASDAQ"),
]

# Sample Treasury bonds for learning
# These are representative examples - in production, would be fetched from Treasury API
TREASURY_BONDS = [
    # (display_name, cusip, coupon_type, coupon_rate, frequency, day_count, issue_date, maturity_date, par)
    (
        "US Treasury 2-Year Note 4.25% 2026",
        "91282CKL7",
        "FIXED",
        Decimal("4.25"),
        "SEMIANNUAL",
        "ACT_ACT",
        date(2024, 1, 31),
        date(2026, 1, 31),
        Decimal("100"),
    ),
    (
        "US Treasury 5-Year Note 4.00% 2029",
        "91282CKM5",
        "FIXED",
        Decimal("4.00"),
        "SEMIANNUAL",
        "ACT_ACT",
        date(2024, 1, 31),
        date(2029, 1, 31),
        Decimal("100"),
    ),
    (
        "US Treasury 10-Year Note 4.125% 2034",
        "91282CKN3",
        "FIXED",
        Decimal("4.125"),
        "SEMIANNUAL",
        "ACT_ACT",
        date(2024, 2, 15),
        date(2034, 2, 15),
        Decimal("100"),
    ),
    (
        "US Treasury 30-Year Bond 4.25% 2054",
        "91282CKP8",
        "FIXED",
        Decimal("4.25"),
        "SEMIANNUAL",
        "ACT_ACT",
        date(2024, 2, 15),
        date(2054, 2, 15),
        Decimal("100"),
    ),
    (
        "US Treasury 26-Week Bill 2025",
        "912797KX1",
        "ZERO",
        None,
        "SEMIANNUAL",  # Not applicable but required
        "ACT_360",
        date(2024, 7, 18),
        date(2025, 1, 16),
        Decimal("100"),
    ),
]


def get_connection():
    """Create a database connection from config."""
    config = load_config()
    return psycopg2.connect(
        host=config.database.postgres.host,
        port=config.database.postgres.port,
        database=config.database.postgres.database,
        user=config.database.postgres.user,
        password=config.database.postgres.password,
    )


def seed_etfs(cur):
    """Insert ETF securities."""
    print("Seeding ETFs...")

    for ticker, display_name, sector, exchange in ETFS:
        security_id = uuid4()

        # Insert into security_registry
        cur.execute(
            """
            INSERT INTO security_registry (security_id, asset_type, currency, display_name)
            VALUES (%s, 'ETF', 'USD', %s)
            ON CONFLICT DO NOTHING
            """,
            (str(security_id), display_name),
        )

        # Insert into equity_details
        cur.execute(
            """
            INSERT INTO equity_details (security_id, ticker, exchange, country, sector)
            VALUES (%s, %s, %s, 'USA', %s)
            ON CONFLICT DO NOTHING
            """,
            (str(security_id), ticker, exchange, sector),
        )

        # Insert identifier (TICKER)
        cur.execute(
            """
            INSERT INTO security_identifier (security_id, id_type, id_value, source, is_primary)
            VALUES (%s, 'TICKER', %s, 'seed', true)
            ON CONFLICT (id_type, id_value) DO NOTHING
            """,
            (str(security_id), ticker),
        )

    print(f"  Inserted {len(ETFS)} ETFs")


def seed_stocks(cur):
    """Insert stock securities."""
    print("Seeding stocks...")

    for ticker, display_name, sector, industry, exchange in STOCKS:
        security_id = uuid4()

        # Insert into security_registry
        cur.execute(
            """
            INSERT INTO security_registry (security_id, asset_type, currency, display_name)
            VALUES (%s, 'EQUITY', 'USD', %s)
            ON CONFLICT DO NOTHING
            """,
            (str(security_id), display_name),
        )

        # Insert into equity_details
        cur.execute(
            """
            INSERT INTO equity_details (security_id, ticker, exchange, country, sector, industry)
            VALUES (%s, %s, %s, 'USA', %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (str(security_id), ticker, exchange, sector, industry),
        )

        # Insert identifier (TICKER)
        cur.execute(
            """
            INSERT INTO security_identifier (security_id, id_type, id_value, source, is_primary)
            VALUES (%s, 'TICKER', %s, 'seed', true)
            ON CONFLICT (id_type, id_value) DO NOTHING
            """,
            (str(security_id), ticker),
        )

    print(f"  Inserted {len(STOCKS)} stocks")


def seed_treasury_bonds(cur):
    """Insert Treasury bond securities."""
    print("Seeding Treasury bonds...")

    for (
        display_name,
        cusip,
        coupon_type,
        coupon_rate,
        frequency,
        day_count,
        issue_date,
        maturity_date,
        par_value,
    ) in TREASURY_BONDS:
        security_id = uuid4()

        # Insert into security_registry
        cur.execute(
            """
            INSERT INTO security_registry (security_id, asset_type, currency, display_name)
            VALUES (%s, 'BOND', 'USD', %s)
            ON CONFLICT DO NOTHING
            """,
            (str(security_id), display_name),
        )

        # Insert into bond_details
        cur.execute(
            """
            INSERT INTO bond_details (
                security_id, issuer_name, coupon_type, coupon_rate,
                payment_frequency, day_count_convention,
                issue_date, maturity_date, par_value
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (
                str(security_id),
                "U.S. Treasury",
                coupon_type,
                coupon_rate,
                frequency,
                day_count,
                issue_date,
                maturity_date,
                par_value,
            ),
        )

        # Insert identifier (CUSIP)
        cur.execute(
            """
            INSERT INTO security_identifier (security_id, id_type, id_value, source, is_primary)
            VALUES (%s, 'CUSIP', %s, 'seed', true)
            ON CONFLICT (id_type, id_value) DO NOTHING
            """,
            (str(security_id), cusip),
        )

    print(f"  Inserted {len(TREASURY_BONDS)} Treasury bonds")


def seed_demo_portfolio(cur):
    """Create a demo portfolio for testing."""
    print("Creating demo portfolio...")

    portfolio_id = uuid4()
    demo_user_id = uuid4()

    cur.execute(
        """
        INSERT INTO portfolio (portfolio_id, user_id, name, base_currency)
        VALUES (%s, %s, %s, 'USD')
        ON CONFLICT DO NOTHING
        RETURNING portfolio_id
        """,
        (str(portfolio_id), str(demo_user_id), "Demo Portfolio"),
    )

    result = cur.fetchone()
    if result:
        print(f"  Created demo portfolio: {portfolio_id}")
        # Initialize cash balance
        cur.execute(
            """
            INSERT INTO cash_balance (portfolio_id, currency, balance)
            VALUES (%s, 'USD', 100000.00)
            ON CONFLICT DO NOTHING
            """,
            (str(portfolio_id),),
        )
        print("  Initialized with $100,000 USD cash balance")
    else:
        print("  Demo portfolio already exists")


def main():
    """Run all seed operations."""
    print("=" * 60)
    print("Seeding security registry...")
    print("=" * 60)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            seed_etfs(cur)
            seed_stocks(cur)
            seed_treasury_bonds(cur)
            seed_demo_portfolio(cur)

        conn.commit()
        print("=" * 60)
        print("Seeding complete!")
        print("=" * 60)

    except Exception as e:
        conn.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
