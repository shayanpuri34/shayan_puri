import fs from 'fs';
import path from 'path';

function parseCSV(content) {
  const lines = content.trim().split('\n');
  if (lines.length < 2) return [];

  function parseLine(line) {
    const values = [];
    let current = '';
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      if (char === '"') {
        if (inQuotes && line[i + 1] === '"') {
          current += '"';
          i++;
        } else {
          inQuotes = !inQuotes;
        }
      } else if (char === ',' && !inQuotes) {
        values.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    values.push(current.trim());
    return values;
  }

  const headers = parseLine(lines[0]);
  const rows = [];
  for (let i = 1; i < lines.length; i++) {
    if (!lines[i].trim()) continue;
    const vals = parseLine(lines[i]);
    const obj = {};
    headers.forEach((h, idx) => {
      const v = vals[idx] !== undefined ? vals[idx] : '';
      const num = Number(v);
      if (v === 'True' || v === 'true') {
        obj[h] = true;
      } else if (v === 'False' || v === 'false') {
        obj[h] = false;
      } else if (v !== '' && !isNaN(num)) {
        obj[h] = num;
      } else {
        obj[h] = v;
      }
    });
    rows.push(obj);
  }
  return rows;
}

try {
  const rootDir = process.cwd();
  const procDir = path.join(rootDir, 'data', 'processed');
  const pubDir = path.join(rootDir, 'public', 'data');
  if (!fs.existsSync(pubDir)) {
    fs.mkdirSync(pubDir, { recursive: true });
  }

  console.log('Reading processed CSV files...');

  const perfMetrics = parseCSV(fs.readFileSync(path.join(procDir, 'performance_metrics.csv'), 'utf8'))[0] || {};
  const eventStudy = parseCSV(fs.readFileSync(path.join(procDir, 'event_study_results.csv'), 'utf8'));
  const robustness = parseCSV(fs.readFileSync(path.join(procDir, 'robustness_results.csv'), 'utf8'));
  const modelComparison = parseCSV(fs.readFileSync(path.join(procDir, 'model_comparison.csv'), 'utf8'));
  const auditReport = parseCSV(fs.readFileSync(path.join(procDir, 'data_leakage_audit.csv'), 'utf8'));
  const sectorResults = parseCSV(fs.readFileSync(path.join(procDir, 'sector_results.csv'), 'utf8'));
  const regimeResults = parseCSV(fs.readFileSync(path.join(procDir, 'regime_results.csv'), 'utf8'));
  const trades = parseCSV(fs.readFileSync(path.join(procDir, 'signal_results.csv'), 'utf8'));
  const events = parseCSV(fs.readFileSync(path.join(procDir, 'earnings_events.csv'), 'utf8'));

  // Parse strategy returns with dates
  const returnsRaw = fs.readFileSync(path.join(procDir, 'strategy_returns.csv'), 'utf8').trim().split('\n');
  const returnsHeader = returnsRaw[0].split(',');
  const returnsData = [];
  
  // Downsample daily returns for charting (take every 2nd or 3rd bar or keep all if reasonable)
  for (let i = 1; i < returnsRaw.length; i++) {
    const parts = returnsRaw[i].split(',');
    // First column is date or index
    const date = parts[0];
    returnsData.push({
      date: date,
      gross_return: Number(parts[1]) || 0,
      transaction_cost: Number(parts[2]) || 0,
      net_return: Number(parts[3]) || 0,
      turnover: Number(parts[4]) || 0,
      long_exposure: Number(parts[5]) || 0,
      short_exposure: Number(parts[6]) || 0,
      gross_exposure: Number(parts[7]) || 0,
      net_exposure: Number(parts[8]) || 0,
      benchmark_return: Number(parts[9]) || 0,
      cumulative_gross: Number(parts[10]) || 0,
      cumulative_net: Number(parts[11]) || 0,
      cumulative_benchmark: Number(parts[12]) || 0,
    });
  }

  // Downsample to ~350 points for super fluid Recharts rendering
  const step = Math.max(1, Math.floor(returnsData.length / 350));
  const equityCurveSampled = [];
  for (let i = 0; i < returnsData.length; i += step) {
    equityCurveSampled.push(returnsData[i]);
  }
  if (returnsData.length > 0 && equityCurveSampled[equityCurveSampled.length - 1] !== returnsData[returnsData.length - 1]) {
    equityCurveSampled.push(returnsData[returnsData.length - 1]);
  }

  // Read report markdown
  let reportMarkdown = '';
  const reportPath = path.join(rootDir, 'reports', 'final_report.md');
  if (fs.existsSync(reportPath)) {
    reportMarkdown = fs.readFileSync(reportPath, 'utf8');
  }

  // Figures catalog
  const figuresDir = path.join(rootDir, 'reports', 'figures');
  let figuresList = [];
  if (fs.existsSync(figuresDir)) {
    const files = fs.readdirSync(figuresDir).filter(f => f.endsWith('.png')).sort();
    figuresList = files.map(file => {
      const id = file.split('_')[0];
      const name = file.replace(/^\d+_/, '').replace(/\.png$/, '').replace(/_/g, ' ');
      let category = 'Event Dynamics';
      if (['07', '08', '09', '10', '11', '12'].includes(id)) category = 'Surprise & PEAD';
      else if (['13', '14'].includes(id)) category = 'Volatility & Volume';
      else if (['15', '16', '17', '18', '19', '20'].includes(id)) category = 'Strategy & Backtest';
      else if (['21', '22'].includes(id)) category = 'Sector & Macro Regime';
      else if (['23', '24', '25'].includes(id)) category = 'Machine Learning';
      else if (['26', '27', '28', '29'].includes(id)) category = 'Risk & Exposure';

      return {
        id,
        filename: file,
        url: `/reports/figures/${file}`,
        title: name.toUpperCase(),
        category
      };
    });
  }

  const resultBundle = {
    generated_at: new Date().toISOString(),
    sample_period: "2016-01-01 to 2024-12-31",
    universe: ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "JPM", "BAC", "XOM", "CVX", "WMT", "COST"],
    metrics: perfMetrics,
    event_study: eventStudy,
    robustness: robustness,
    model_comparison: modelComparison,
    audit_report: auditReport,
    sector_results: sectorResults,
    regime_results: regimeResults,
    trades: trades,
    events_sample: events.slice(0, 100), // first 100 for table preview
    total_events_count: events.length,
    equity_curve: equityCurveSampled,
    figures: figuresList,
    report_markdown: reportMarkdown
  };

  const outFile = path.join(pubDir, 'engine_data.json');
  fs.writeFileSync(outFile, JSON.stringify(resultBundle, null, 2), 'utf8');
  console.log(`Successfully generated ${outFile} (${(fs.statSync(outFile).size / 1024).toFixed(1)} KB)`);
} catch (err) {
  console.error('Error generating engine_data.json:', err);
  process.exit(1);
}
