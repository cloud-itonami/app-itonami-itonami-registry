'use strict';

// Short Japanese labels for the ISIC classes represented in the association catalog.
const industries = {
  '0126': '油料果実栽培',
  '0150': '耕種・畜産の混合農業',
  '0610': '原油採掘',
  '2011': '基礎化学品製造',
  '2100': '医薬品製造',
  '2910': '自動車製造',
  '3510': '発電・送配電',
  '3600': '取水・浄水・給水',
  '4100': '建築工事',
  '4719': 'その他の総合小売',
  '4923': '道路貨物輸送',
  '5010': '海上・沿岸輸送',
  '5110': '航空旅客輸送',
  '5510': '短期宿泊',
  '5610': '飲食店・移動飲食サービス',
  '6020': 'テレビ番組制作・放送',
  '6120': '無線通信',
  '6201': 'コンピュータプログラミング',
  '6411': '中央銀行',
  '6419': '銀行・その他金融仲介',
  '6492': 'その他の信用供与',
  '6511': '生命保険',
  '6512': '損害保険',
  '6612': '証券・商品取引仲介',
  '6810': '不動産の売買・賃貸',
  '6910': '法務サービス',
  '6920': '会計・監査・税務',
  '8621': '医科診療',
  '9411': '経済・経営者団体',
};

const filters = document.getElementById('filters');
const form = filters.querySelector('form');
const country = document.getElementById('country');
const industry = document.getElementById('industry');
const results = document.getElementById('results');
const status = document.getElementById('status');
const regions = typeof Intl.DisplayNames === 'function' ? new Intl.DisplayNames('ja', {type: 'region'}) : null;

function make(tag, text, className) {
  const element = document.createElement(tag);
  if (text != null) element.textContent = text;
  if (className) element.className = className;
  return element;
}

function externalLink(url, text) {
  const anchor = make('a', text);
  anchor.href = url;
  anchor.target = '_blank';
  anchor.rel = 'noopener noreferrer';
  return anchor;
}

function countryLabel({country, countryAlpha2}) {
  if (!country) return '国・地域未確認';
  const name = regions && /^[A-Z]{2}$/.test(countryAlpha2) ? regions.of(countryAlpha2) : country;
  return name === country ? country : `${name}（${country}）`;
}

function industryLabel(code) {
  if (!code) return '業種未確認';
  return industries[code] ? `${code} · ${industries[code]}` : code;
}

function setOptions(select, labels) {
  const options = [...labels].sort((a, b) => a[1].localeCompare(b[1], 'ja'));
  for (const [value, label] of options) select.add(new Option(label, value));
}

function citation(url, provenance, label) {
  const host = new URL(url).host;
  const line = make('p');
  line.append(externalLink(url, `${label}（${host}）`));
  if (provenance) line.append(make('span', ` · ${provenance}`, 'meta'));
  return line;
}

function ruleItem(rule) {
  const item = make('li');
  item.append(make('h3', rule.title));
  const dates = [rule.kind.replaceAll('-', ' '), `取得日 ${rule.retrievedAt}`];
  if (rule.establishedAt) dates.push(`制定・設立 ${rule.establishedAt}`);
  if (rule.revisedAt) dates.push(`改訂 ${rule.revisedAt}`);
  item.append(make('p', dates.join(' · '), 'meta'));
  if (rule.article) item.append(make('p', `参照箇所 ${rule.article}`));
  item.append(citation(rule.url, rule.provenance, '出典を開く'));
  if (rule.corroboratingUrl) {
    item.append(citation(rule.corroboratingUrl, rule.corroboratingProvenance, '補足出典を開く'));
  }
  return item;
}

function associationCard(association) {
  const {name, rules, repository, commit, license, rulesSha256, archived} = association;
  const details = make('details');
  const summary = make('summary');
  const count = rules === null ? 'データ未検証' : `${rules.length}件の記録`;
  const metadata = [countryLabel(association), industryLabel(association.isic), count];
  summary.append(make('strong', name), make('span', metadata.join(' · '), 'meta'));
  details.append(summary);
  details.addEventListener('toggle', () => {
    const content = make('div', null, 'details-body');
    if (rules?.length) {
      const list = make('ul', null, 'rules');
      for (const rule of rules) list.append(ruleItem(rule));
      content.append(list);
    } else {
      const reason = rules === null ? '検証済みのルールデータがありません。' : '収録されているルールや活動の記録はありません。';
      content.append(make('p', reason));
    }
    const footer = make('footer', null, 'meta');
    const base = `https://github.com/${repository}`;
    const url = rulesSha256 ? `${base}/blob/${commit}/data/datascript-tx.edn` : `${base}/tree/${commit}`;
    const label = rulesSha256 ? '収録データ（固定コミット）' : '元リポジトリ（固定コミット）';
    footer.append(externalLink(url, label), ` · ${license}`);
    if (archived) footer.append(' · アーカイブ');
    content.append(footer);
    details.append(content);
  }, {once: true});
  return details;
}

function init() {
  const {associations, observedOn} = JSON.parse(document.getElementById('assoc-data').textContent);
  const countries = new Map();
  const sectors = new Map();
  for (const association of associations) {
    if (association.country) countries.set(association.country, countryLabel(association));
    if (association.isic) sectors.set(association.isic, industryLabel(association.isic));
  }
  setOptions(country, countries);
  setOptions(industry, sectors);
  document.getElementById('snapshot').textContent = `カタログ確認日 ${observedOn}`;

  function render(countryCode = '', industryCode = '') {
    const matches = associations.filter((association) =>
      (!countryCode || association.country === countryCode) &&
      (!industryCode || association.isic === industryCode));
    results.replaceChildren(...matches.map(associationCard));
    status.textContent = matches.length
      ? `${matches.length} / ${associations.length} 団体`
      : '条件に一致する団体はありません。';
  }

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    render(country.value, industry.value);
  });
  form.addEventListener('reset', () => render());
  filters.hidden = false;
  render();
}

try {
  init();
} catch (error) {
  status.textContent = '業界団体カタログを読み込めませんでした。';
  console.error(error);
}
