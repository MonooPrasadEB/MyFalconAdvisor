#!/usr/bin/env python3
"""
One-time script to classify sectors for all portfolio assets.

This script uses OpenAI to classify the sector for each stock/ETF in the portfolio_assets table
and updates the sector column in the database.
"""

import sys
from pathlib import Path

# Add the parent directory to path
sys.path.append(str(Path(__file__).parent))

from myfalconadvisor.tools.database_service import DatabaseService
from myfalconadvisor.core.config import Config
from langchain_openai import ChatOpenAI
from sqlalchemy import text

def classify_stock_sector(symbol: str, llm: ChatOpenAI) -> str:
    """Use AI to classify stock sector."""
    try:
        # Simple sector classification prompt
        prompt = f"""
Classify the stock symbol '{symbol}' into ONE of these sectors:
- Technology
- Healthcare  
- Financial Services
- Consumer Discretionary
- Consumer Staples
- Energy
- Utilities
- Real Estate
- Materials
- Industrials
- Communication Services
- Other

For ETFs, classify by primary focus:
- SPY, VTI, VOO = Other (broad market)
- QQQ = Technology
- BND, AGG = Other (bonds)
- XLF = Financial Services
- XLK = Technology
- XLE = Energy

Respond with ONLY the sector name, nothing else.
"""
        
        response = llm.invoke(prompt)
        sector = response.content.strip()
        
        # Validate sector
        valid_sectors = [
            "Technology", "Healthcare", "Financial Services", 
            "Consumer Discretionary", "Consumer Staples", "Energy",
            "Utilities", "Real Estate", "Materials", "Industrials",
            "Communication Services", "Other"
        ]
        
        if sector in valid_sectors:
            return sector
        else:
            print(f"  ⚠️  Invalid sector '{sector}' for {symbol}, defaulting to 'Other'")
            return "Other"
            
    except Exception as e:
        print(f"  ❌ Error classifying {symbol}: {e}")
        return "Other"


def main():
    """Main function to classify all portfolio assets."""
    print("🏷️  MyFalconAdvisor Sector Classification Script")
    print("=" * 60)
    
    # Initialize services
    config = Config.get_instance()
    db_service = DatabaseService()
    
    # Initialize OpenAI
    llm = ChatOpenAI(
        model=config.default_model,
        temperature=0.0,  # Deterministic for classification
        api_key=config.openai_api_key
    )
    
    print(f"🤖 Using OpenAI model: {config.default_model}")
    print()
    
    try:
        # Get all unique symbols from portfolio_assets
        with db_service.get_session() as session:
            result = session.execute(text("""
                SELECT DISTINCT symbol 
                FROM portfolio_assets 
                WHERE sector IS NULL OR sector = '' OR sector = 'Other'
                ORDER BY symbol
            """))
            
            symbols = [row[0] for row in result.fetchall()]
            
            if not symbols:
                print("✅ All assets already have sector classifications!")
                return
            
            print(f"📊 Found {len(symbols)} symbols to classify:")
            for symbol in symbols:
                print(f"  • {symbol}")
            print()
            
            # Classify each symbol
            classified_count = 0
            for i, symbol in enumerate(symbols, 1):
                print(f"[{i}/{len(symbols)}] Classifying {symbol}...", end=" ")
                
                # Get sector from LLM
                sector = classify_stock_sector(symbol, llm)
                print(f"→ {sector}")
                
                # Update database
                update_result = session.execute(text("""
                    UPDATE portfolio_assets 
                    SET sector = :sector 
                    WHERE symbol = :symbol
                """), {"sector": sector, "symbol": symbol})
                
                rows_updated = update_result.rowcount
                print(f"  (updated {rows_updated} rows)")
                classified_count += 1
            
            # Commit all changes
            print()
            print("💾 Committing changes to database...")
            session.commit()
            print("✅ Commit successful!")
            print()
            print(f"✅ Successfully classified {classified_count} symbols!")
            print()
            
            # Show summary
            print("📋 Classification Summary:")
            result = session.execute(text("""
                SELECT sector, COUNT(*) as count
                FROM portfolio_assets
                GROUP BY sector
                ORDER BY count DESC
            """))
            
            for row in result.fetchall():
                print(f"  {row[0]}: {row[1]} assets")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print()
    print("🎉 Sector classification complete!")


if __name__ == "__main__":
    main()

