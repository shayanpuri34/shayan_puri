export interface PerformanceMetrics {
  Total_Return: number;
  CAGR: number;
  Annualized_Volatility: number;
  Sharpe_Ratio: number;
  Sortino_Ratio: number;
  Calmar_Ratio: number;
  Maximum_Drawdown: number;
  Win_Rate: number;
  Profit_Factor: number;
  Average_Trade: number;
  Median_Trade: number;
  Best_Trade: number;
  Worst_Trade: number;
  VaR_95_Daily: number;
  VaR_99_Daily: number;
  CVaR_95_Daily: number;
  CVaR_99_Daily: number;
  Annualized_Turnover: number;
  Average_Gross_Exposure: number;
  Average_Net_Exposure: number;
  Total_Trades: number;
}

export interface EventStudyWindow {
  Window: string;
  N: number;
  Mean_CAR: number;
  Median_CAR: number;
  Std_Dev: number;
  t_statistic: number;
  p_value: number;
  CI_95_Lower: number;
  CI_95_Upper: number;
  Significant_5pct: boolean;
}

export interface RobustnessRow {
  Specification: string;
  Holding_Period: string;
  Cost_bps: number;
  CAGR: number;
  Sharpe: number;
  Max_Drawdown: number;
  Win_Rate: number;
  Total_Trades: number;
}

export interface MLModelRow {
  Model: string;
  Type: string;
  Directional_Accuracy: number;
  AUC?: number;
  Precision?: number;
  Recall?: number;
  F1?: number;
  MAE?: number;
  RMSE?: number;
  R2?: number;
}

export interface LeakageAuditCheck {
  Check_ID: number | string;
  Audit_Check: string;
  Status: string;
  Details: string;
}

export interface SectorResult {
  Sector: string;
  Total_Events: number;
  Avg_Surprise_Pct: number;
  "Avg_CAR[0,+1]": number;
  "Avg_PEAD_CAR[+1,+5]": number;
  Strategy_Trades: number;
  Avg_Trade_Return: number;
  Trade_Win_Rate: number;
}

export interface RegimeResult {
  Regime_Type: string;
  Regime: string;
  Days: number;
  Ann_Return: number;
  Ann_Volatility: number;
  Sharpe_Ratio: number;
  Daily_Win_Rate: number;
}

export interface TradeRecord {
  ticker: string;
  announcement_date: string;
  timing_class: string;
  entry_date: string;
  exit_date: string;
  signal: number;
  position_dir: number;
  entry_price: number;
  exit_price: number;
  holding_period_days: number;
  gross_return: number;
  transaction_cost: number;
  net_return: number;
  market_return: number;
  abnormal_return: number;
}

export interface EquityCurvePoint {
  date: string;
  gross_return: number;
  transaction_cost: number;
  net_return: number;
  turnover: number;
  long_exposure: number;
  short_exposure: number;
  gross_exposure: number;
  net_exposure: number;
  benchmark_return: number;
  cumulative_gross: number;
  cumulative_net: number;
  cumulative_benchmark: number;
}

export interface FigureItem {
  id: string;
  filename: string;
  url: string;
  title: string;
  category: string;
}

export interface EngineData {
  generated_at: string;
  sample_period: string;
  universe: string[];
  metrics: PerformanceMetrics;
  event_study: EventStudyWindow[];
  robustness: RobustnessRow[];
  model_comparison: MLModelRow[];
  audit_report: LeakageAuditCheck[];
  sector_results: SectorResult[];
  regime_results: RegimeResult[];
  trades: TradeRecord[];
  events_sample: Record<string, any>[];
  total_events_count: number;
  equity_curve: EquityCurvePoint[];
  figures: FigureItem[];
  report_markdown: string;
}

export type TabKey =
  | 'performance'
  | 'event_study'
  | 'pead'
  | 'ml_models'
  | 'robustness'
  | 'regime_sector'
  | 'leakage_audit'
  | 'trades'
  | 'figures'
  | 'report';
