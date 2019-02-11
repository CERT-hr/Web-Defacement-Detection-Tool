
DEF MAXSTRINGLEN = 1000

def compare(char *X, char *Y):

    cdef int m = len(X), n = len(Y)

    cdef short C[MAXSTRINGLEN + 1][MAXSTRINGLEN + 1]

    for i in range(0, m+1):
        C[i][0] = 0

    for j in range(0, n+1):
        C[0][j] = 0

    for i in range(1, m+1):
        for j in range(1, n+1):

            if X[i-1] == Y[j-1]:
                C[i][j] = C[i-1][j-1] + 1
            else:
                C[i][j] = max(C[i][j-1], C[i-1][j])

    return 2.0 * C[m][n] / (n + m)

