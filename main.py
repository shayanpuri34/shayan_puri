"""Main entry point to execute the Event-Driven Earnings Alpha & Backtesting Engine."""

import sys
from src.pipeline import EarningsAlphaPipeline

if __name__ == "__main__":
    print("=" * 70)
    print("STARTING EVENT-DRIVEN EARNINGS ALPHA & BACKTESTING ENGINE")
    print("=" * 70)

    try:
        pipeline = EarningsAlphaPipeline()
        results = pipeline.run()

        print("\n" + "=" * 70)
        print("RESEARCH PIPELINE EXECUTION COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"Total Corporate Events Analyzed : {results['events_count']}")
        print(f"Total Executed Strategy Trades  : {results['trades_count']}")
        print(f"Base Strategy CAGR              : {results['metrics'].get('CAGR', 0)*100:.2f}%")
        print(f"Annualized Sharpe Ratio         : {results['metrics'].get('Sharpe_Ratio', 0):.3f}")
        print(f"Maximum Drawdown                : {results['metrics'].get('Maximum_Drawdown', 0)*100:.2f}%")
        print(f"Win Rate                        : {results['metrics'].get('Win_Rate', 0)*100:.2f}%")
        print(f"Profit Factor                   : {results['metrics'].get('Profit_Factor', 0):.2f}")
        print(f"15-Point Leakage Audit Status   : {'PASSED (Zero Leaks)' if results['audit_passed'] else 'FAILED'}")
        print(f"Generated Visualizations        : {results['figures_count']} publication figures")
        print(f"Full Research Report Path       : {results['report_path']}")
        print("=" * 70)

    except Exception as e:
        print(f"\n[CRITICAL ERROR] Pipeline execution failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
