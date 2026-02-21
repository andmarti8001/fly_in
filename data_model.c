#include <stdio.h>

#define N_HUBS 3
#define T 3
#define M_RESTRICTED 1

#define HUB_TIME_COUNT ((T+1) * N_HUBS)
#define HUB_SPLIT_COUNT (2 * HUB_TIME_COUNT)
#define TRANSIT_OFFSET HUB_SPLIT_COUNT
#define TRANSIT_COUNT ((T+1) * M_RESTRICTED)

#define TOTAL_NODES (HUB_SPLIT_COUNT + TRANSIT_COUNT)

#define MAX_EDGES 128

typedef struct {
    int to;
    int cap;
} Edge;

typedef struct {
    Edge edges[MAX_EDGES];
    int count;
} AdjList;

AdjList graph[TOTAL_NODES];   // <-- Entire expanded graph on stack

// -------- ID HELPERS --------

int hub_time(int u, int t) {
    return t * N_HUBS + u;
}

int IN(int u, int t) {
    return 2 * hub_time(u, t);
}

int OUT(int u, int t) {
    return 2 * hub_time(u, t) + 1;
}

int TRANSIT(int eid, int t_wait) {
    return TRANSIT_OFFSET + t_wait * M_RESTRICTED + eid;
}

// -------- Add Edge --------

void add_edge(int from, int to, int cap) {
    graph[from].edges[graph[from].count].to = to;
    graph[from].edges[graph[from].count].cap = cap;
    graph[from].count++;
}

// -------- Build Example --------

void build_example() {

    // 1) Node split edges (hub capacity = 1)
    for (int t = 0; t <= T; t++) {
        for (int u = 0; u < N_HUBS; u++) {
            add_edge(IN(u,t), OUT(u,t), 1);
        }
    }

    // 2) Wait edges (allowed only at hub 0 and 2)
    for (int t = 0; t < T; t++) {

        // hub 0 wait
        add_edge(OUT(0,t), IN(0,t+1), 100);

        // hub 2 wait
        add_edge(OUT(2,t), IN(2,t+1), 100);
    }

    // 3) Restricted edge 0 -> 1
    int eid = 0;

    for (int t = 0; t <= T-2; t++) {

        // Step 1: enter transit at t+1
        add_edge(OUT(0,t), TRANSIT(eid, t+1), 1);

        // Step 2: forced entry at t+2
        add_edge(TRANSIT(eid, t+1), IN(1,t+2), 100);
    }

    // 4) Normal edge 1 -> 2
    for (int t = 0; t < T; t++) {
        add_edge(OUT(1,t), IN(2,t+1), 1);
    }
}

// -------- Debug Print --------

void print_graph() {
    for (int i = 0; i < TOTAL_NODES; i++) {
        if (graph[i].count == 0) continue;

        printf("Node %d:\n", i);
        for (int j = 0; j < graph[i].count; j++) {
            printf("   -> %d (cap=%d)\n",
                   graph[i].edges[j].to,
                   graph[i].edges[j].cap);
        }
    }
}

int main() {

    build_example();
    print_graph();

    return 0;
}

