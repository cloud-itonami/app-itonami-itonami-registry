"""Retired repository names: GitHub transfer renames, alias -> canonical owner/name.

Verified 2026-11-22 with `gh api repos/<owner>/<name>` (KOTOBA-159): each alias
resolves to the canonical `full_name` with the same numeric repo id (comment).
The catalogs keep only the canonical name; validate.py refuses the aliases and
the blueprint builder normalizes `--add` through this table when GitHub is
unreachable. Re-verify with `gh api` before extending this table.
"""
RETIRED = {
    'cloud-itonami/app-itonami-adserver': 'network-awai/app-itonami-adserver',  # id 1295986713
    'cloud-itonami/app-itonami-kotobase-storage-d1': 'network-awai/app-itonami-kotobase-storage-d1',  # id 1312638976
    'cloud-itonami/app-itonami-yataverse': 'network-awai/app-itonami-yataverse',  # id 1396729537
    'network-awai/app-itonami-abaki': 'cloud-itonami/app-itonami-abaki',  # id 1303678830
    'network-awai/app-itonami-agent-trace': 'cloud-itonami/app-itonami-agent-trace',  # id 1462694907
    'network-awai/app-itonami-arbitrage': 'cloud-itonami/app-itonami-arbitrage',  # id 1305795714
    'network-awai/app-itonami-bunsho': 'cloud-itonami/app-itonami-bunsho',  # id 1305926707
    'network-awai/app-itonami-cloud-itonami-isic-6810': 'cloud-itonami/app-itonami-cloud-itonami-isic-6810',  # id 1285564674
    'network-awai/app-itonami-explorer': 'cloud-itonami/app-itonami-explorer',  # id 1305926652
    'network-awai/app-itonami-hakkou': 'cloud-itonami/app-itonami-hakkou',  # id 1305870808
    'network-awai/app-itonami-hibiki': 'cloud-itonami/app-itonami-hibiki',  # id 1303651163
    'network-awai/app-itonami-hirameki-etz': 'cloud-itonami/app-itonami-hirameki-etz',  # id 1303664710
    'network-awai/app-itonami-hyokeisan': 'cloud-itonami/app-itonami-hyokeisan',  # id 1305930290
    'network-awai/app-itonami-icc': 'cloud-itonami/app-itonami-icc',  # id 1341951968
    'network-awai/app-itonami-kabi': 'cloud-itonami/app-itonami-kabi',  # id 1305803051
    'network-awai/app-itonami-kaikei': 'cloud-itonami/app-itonami-kaikei',  # id 1305809529
    'network-awai/app-itonami-karute': 'cloud-itonami/app-itonami-karute',  # id 1305922980
    'network-awai/app-itonami-ki': 'cloud-itonami/app-itonami-ki',  # id 1305891334
    'network-awai/app-itonami-kinoko': 'cloud-itonami/app-itonami-kinoko',  # id 1305803211
    'network-awai/app-itonami-kiyome': 'cloud-itonami/app-itonami-kiyome',  # id 1305820713
    'network-awai/app-itonami-kobo': 'cloud-itonami/app-itonami-kobo',  # id 1305803287
    'network-awai/app-itonami-koke': 'cloud-itonami/app-itonami-koke',  # id 1305866317
    'network-awai/app-itonami-kumade': 'cloud-itonami/app-itonami-kumade',  # id 1436852542
    'network-awai/app-itonami-manabi-cert-prep': 'cloud-itonami/app-itonami-manabi-cert-prep',  # id 1305843120
    'network-awai/app-itonami-maps': 'cloud-itonami/app-itonami-maps',  # id 1305942545
    'network-awai/app-itonami-market': 'cloud-itonami/app-itonami-market',  # id 1305803431
    'network-awai/app-itonami-market-android': 'cloud-itonami/app-itonami-market-android',  # id 1463402671
    'network-awai/app-itonami-minori': 'cloud-itonami/app-itonami-minori',  # id 1303894535
    'network-awai/app-itonami-mold-allergy': 'cloud-itonami/app-itonami-mold-allergy',  # id 1305820819
    'network-awai/app-itonami-nagare': 'cloud-itonami/app-itonami-nagare',  # id 1461731453
    'network-awai/app-itonami-omikuji': 'cloud-itonami/app-itonami-omikuji',  # id 1305820859
    'network-awai/app-itonami-open-ossekai': 'cloud-itonami/app-itonami-open-ossekai',  # id 1305833356
    'network-awai/app-itonami-organism-viz': 'cloud-itonami/app-itonami-organism-viz',  # id 1305960647
    'network-awai/app-itonami-otakiage': 'cloud-itonami/app-itonami-otakiage',  # id 1305833443
    'network-awai/app-itonami-reuse': 'cloud-itonami/app-itonami-reuse',  # id 1462132876
    'network-awai/app-itonami-rodo': 'cloud-itonami/app-itonami-rodo',  # id 1461674741
    'network-awai/app-itonami-saikin': 'cloud-itonami/app-itonami-saikin',  # id 1305803773
    'network-awai/app-itonami-seibutsu': 'cloud-itonami/app-itonami-seibutsu',  # id 1305854327
    'network-awai/app-itonami-shinka': 'cloud-itonami/app-itonami-shinka',  # id 1305803851
    'network-awai/app-itonami-tawami': 'cloud-itonami/app-itonami-tawami',  # id 1303723627
    'network-awai/app-itonami-tomoshibi': 'cloud-itonami/app-itonami-tomoshibi',  # id 1290705311
    'network-awai/app-itonami-torifune': 'cloud-itonami/app-itonami-torifune',  # id 1279065082
    'network-awai/app-itonami-torihiki': 'cloud-itonami/app-itonami-torihiki',  # id 1448874932
    'network-awai/app-itonami-tsumugi': 'cloud-itonami/app-itonami-tsumugi',  # id 1279065775
    'network-awai/app-itonami-umisachi': 'cloud-itonami/app-itonami-umisachi',  # id 1279129473
    'network-awai/app-itonami-wakai': 'cloud-itonami/app-itonami-wakai',  # id 1279132161
    'network-awai/app-itonami-yudane': 'cloud-itonami/app-itonami-yudane',  # id 1303727554
    'network-awai/app-itonami-zuhyo': 'cloud-itonami/app-itonami-zuhyo',  # id 1305795287
}


def canonical(repository):
    """Redirect-resolved repository name (KOTOBA-159): the canonical owner/name."""
    return RETIRED.get(repository, repository)
