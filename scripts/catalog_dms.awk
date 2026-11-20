# catalog_dms.awk -- inventario dos conjuntos DMS do benchmark MULTI-evolve
#
# Uso:  awk -f scripts/catalog_dms.awk data/external/zenodo-17620759/*.csv
#
# Para cada arquivo CSV (esquema ProteinGym: mutant,mutated_sequence,DMS_score,DMS_score_bin)
# reporta: n de variantes, distribuicao por ordem mutacional, ordem maxima,
# posicoes distintas mutadas, mutacoes unicas observadas e completude combinatoria
# aparente. A ordem mutacional e o numero de tokens separados por ':' no campo 'mutant'.
#
# Saida: TSV com uma linha por arquivo.

BEGIN {
    FS = ","
    OFS = "\t"
    print "dataset", "n_variantes", "ordem_max", "n_pos_distintas", "n_muts_unicas", \
          "n_ordem1", "n_ordem2", "n_ordem3", "n_ordem4", "n_ordem5+", \
          "score_min", "score_max"
}

FNR == 1 { next }   # pula cabecalho

{
    mut = $1
    if (mut == "" || mut == "WT") next

    # ordem mutacional = numero de tokens separados por ':'
    n = split(mut, toks, ":")
    order[FILENAME, n]++
    total[FILENAME]++
    if (n > maxord[FILENAME]) maxord[FILENAME] = n

    # posicoes e mutacoes unicas
    for (i = 1; i <= n; i++) {
        tok = toks[i]
        pos = tok
        gsub(/[^0-9]/, "", pos)
        if (pos != "") {
            if (!((FILENAME, pos) in seenpos)) { seenpos[FILENAME, pos] = 1; npos[FILENAME]++ }
        }
        if (!((FILENAME, tok) in seenmut)) { seenmut[FILENAME, tok] = 1; nmut[FILENAME]++ }
    }

    # faixa de score (campo 3)
    s = $3 + 0
    if (!(FILENAME in haves)) { smin[FILENAME] = s; smax[FILENAME] = s; haves[FILENAME] = 1 }
    if (s < smin[FILENAME]) smin[FILENAME] = s
    if (s > smax[FILENAME]) smax[FILENAME] = s
}

END {
    for (f in total) {
        base = f
        sub(/.*[\/\\]/, "", base)
        sub(/\.csv$/, "", base)

        high = 0
        for (k = 5; k <= maxord[f]; k++) high += order[f, k]

        printf "%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%.4f\t%.4f\n", \
            base, total[f], maxord[f], npos[f], nmut[f], \
            order[f,1]+0, order[f,2]+0, order[f,3]+0, order[f,4]+0, high, \
            smin[f], smax[f]
    }
}
