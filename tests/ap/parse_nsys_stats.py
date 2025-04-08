import sys
import sqlite3
from collections import defaultdict
import numpy as np

'''
CREATE TABLE CUPTI_ACTIVITY_KIND_KERNEL (
    start                       INTEGER   NOT NULL,                    -- Event start timestamp (ns).
    end                         INTEGER   NOT NULL,                    -- Event end timestamp (ns).
    deviceId                    INTEGER   NOT NULL,                    -- Device ID.
    contextId                   INTEGER   NOT NULL,                    -- Context ID.
    greenContextId              INTEGER,                               -- Green context ID.
    streamId                    INTEGER   NOT NULL,                    -- Stream ID.
    correlationId               INTEGER,                               -- REFERENCES CUPTI_ACTIVITY_KIND_RUNTIME(correlationId)
    globalPid                   INTEGER,                               -- Serialized GlobalId.
    demangledName               INTEGER   NOT NULL,                    -- REFERENCES StringIds(id) -- Kernel function name w/ templates
    shortName                   INTEGER   NOT NULL,                    -- REFERENCES StringIds(id) -- Base kernel function name
    mangledName                 INTEGER,                               -- REFERENCES StringIds(id) -- Raw C++ mangled kernel function name
    launchType                  INTEGER,                               -- REFERENCES ENUM_CUDA_KERNEL_LAUNCH_TYPE(id)
    cacheConfig                 INTEGER,                               -- REFERENCES ENUM_CUDA_FUNC_CACHE_CONFIG(id)
    registersPerThread          INTEGER   NOT NULL,                    -- Number of registers required for each thread executing the kernel.
    gridX                       INTEGER   NOT NULL,                    -- X-dimension grid size.
    gridY                       INTEGER   NOT NULL,                    -- Y-dimension grid size.
    gridZ                       INTEGER   NOT NULL,                    -- Z-dimension grid size.
    blockX                      INTEGER   NOT NULL,                    -- X-dimension block size.
    blockY                      INTEGER   NOT NULL,                    -- Y-dimension block size.
    blockZ                      INTEGER   NOT NULL,                    -- Z-dimension block size.
    staticSharedMemory          INTEGER   NOT NULL,                    -- Static shared memory allocated for the kernel (B).
    dynamicSharedMemory         INTEGER   NOT NULL,                    -- Dynamic shared memory reserved for the kernel (B).
    localMemoryPerThread        INTEGER   NOT NULL,                    -- Amount of local memory reserved for each thread (B).
    localMemoryTotal            INTEGER   NOT NULL,                    -- Total amount of local memory reserved for the kernel (B).
    gridId                      INTEGER   NOT NULL,                    -- Unique grid ID of the kernel assigned at runtime.
    sharedMemoryExecuted        INTEGER,                               -- Shared memory size set by the driver.
    graphNodeId                 INTEGER,                               -- REFERENCES CUDA_GRAPH_NODE_EVENTS(graphNodeId)
    sharedMemoryLimitConfig     INTEGER                                -- REFERENCES ENUM_CUDA_SHARED_MEM_LIMIT_CONFIG(id)
);
CREATE TABLE StringIds (
    id                          INTEGER   NOT NULL   PRIMARY KEY,      -- ID reference value.
    value                       TEXT      NOT NULL                     -- String value.
);
'''

ignore_kern = set('''\
dctQuantInvJpegKernel
ycbcr_to_format_kernel_roi
BatchedSeparableResampleKernel
'''.splitlines())

def add_comma(s):
    if isinstance(s, float):
        s = round(s)
    if isinstance(s, int):
        s = str(s)
    return ','.join(s[max(0, i-3):i] for i in range(len(s)%3 or 3, len(s)+1, 3))

class KernelTrace:
    def __init__(self, path, file_id, start=None, end=None):
        print('loading trace:', path, file=sys.stderr)
        db = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
        string_ids = {k: v for k, v in db.execute('SELECT * FROM StringIds')}
        total_time = 0
        start = 0 if start is None else round(start * 1e9)
        end = -1 if end is None else round(end * 1e9)

        cur = db.execute('SELECT * FROM CUPTI_ACTIVITY_KIND_KERNEL ORDER BY start')
        traces = []
        for row in cur:
            row = list(row)
            if row[0] < start:
                continue
            if end >= 0 and row[1] >= end:
                continue
            total_time += row[1] - row[0]
            row[8] = string_ids[row[8]] + '<<<%d, %d, %d, %d, %d, %d, %d>>>' % (*row[14:20], row[21])  # demangledName
            row[9] = string_ids[row[9]]  # shortName
            traces.append(row)

        self.string_ids = string_ids
        self.traces = traces
        self.total_time = total_time
        avg_time = total_time / 151.0 / 1e6
        print('avg_time: ', avg_time)
        for row in self.traces:
            print(row)
        with open('/work/PaddleTest/xzc_output/time.txt', 'a') as f:
            print(path.split('/')[-1].split('_')[-2], "%.4f" % avg_time, file_id, file=f)

    def rm_outlier_mean(self, path, min_start=None):
        print('loading trace:', path, file=sys.stderr)
        db = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
        string_ids = {k: v for k, v in db.execute('SELECT * FROM StringIds')}
        total_time = 0
        total_cnt = 0

        cur = db.execute(
            'SELECT * FROM CUPTI_ACTIVITY_KIND_KERNEL ORDER BY start')
        traces = []
        cnt_cyc_dict = dict()
        cyc_flag = None
        total_time_list = []
        cyc_time = 0
        for row in cur:
            row = list(row)
            row[9] = string_ids[row[9]]  # shortName
            if row[9] in ignore_kern:
                continue
            if min_start is not None and row[0] < min_start:  # start
                continue
            dname = string_ids[row[8]]  # demangledName
            row[8] = dname + '<<<%d, %d, %d, %d, %d, %d, %d>>>' % (*row[14:20], row[21])
            if row[8] not in list(cnt_cyc_dict.keys()):
                cnt_cyc_dict[row[8]] = 1
            else:
                cnt_cyc_dict[row[8]] += 1
                if (cnt_cyc_dict[row[8]] == 31):
                    if cyc_flag is None:
                        cyc_flag = row[8]
                    cyc_time += row[1] - row[0]
                if (cnt_cyc_dict[row[8]] > 31):
                    if cyc_flag == row[8]:
                        total_cnt += 1
                        total_time_list.append(cyc_time)
                        cyc_time = 0
                    cyc_time += row[1] - row[0]
            traces.append(row)
        total_time_list.append(cyc_time)
        times = np.array(total_time_list)
        extracted_times = times[times < np.percentile(times, 82)]
        extracted_times2 = extracted_times[extracted_times > np.percentile(extracted_times, 8)]
        dev_time = np.mean(extracted_times2)
        print("%.4f" % float(dev_time/1e6))
        print(total_time_list)
        print(total_cnt)
        print(cyc_flag)
        self.string_ids = string_ids
        self.traces = traces
        self.total_time = total_time
        print(total_cnt)
        print(total_time/float(total_cnt)/1e6)
        for row in self.traces:
                print(row)

    def dump(self, path):
        with open(path, 'w') as f:
            for row in self.traces:
                print(row[8], file=f)

    def print_cutlass_stats(self):
        exit(0)
        cutlass_total_time = 0
        cutlass_cnt = 0.0
        kernel_total_time = defaultdict(lambda: [0, 0])  # time, count
        for row in self.traces:
            if row[8].startswith('void cutlass::Kernel'):
                cutlass_total_time += (t := row[1] - row[0])
                cutlass_cnt += 1
                kernel_total_time[row[8]][0] += t
                kernel_total_time[row[8]][1] += 1
        print('total_time: ', total_time / 10.0 / 10e6)
        print(cutlass_total_time)
        print('Cutlass Total Time (ns): %.4f' % (int(cutlass_total_time) / cutlass_cnt))
        print('Cutlass Total Time (%%): %.2f' % (cutlass_total_time / self.total_time * 100))
        print('Cum Time (%)\tTotal Time (%)\tAvg Time (us)\tReduce?\tKernel Name')

        kernel_total_time = sorted(kernel_total_time.items(), key=lambda i: -i[1][0])
        acc_ratio = 0
        for name, (t, cnt) in kernel_total_time[:100]:
            acc_ratio += (ratio := t / self.total_time)
            is_reduce = 'reduce' in name
            if (i := name.find('__COND')) != -1:
                name = name[:i]
            if len(name) > 60:
                name = f'[{name[:57]}...]()'
            print('%.2f\t%.2f\t%s\t%s\t%s' % (
                acc_ratio * 100, ratio * 100, add_comma(str(round(t / (cnt*1000)))),
                'Yes' if is_reduce else '', name
            ))

    def print_fn_stats(self):
        cinn_total_time = 0
        reduce_total_time = 0
        kernel_total_time = defaultdict(lambda: [0, 0])  # time, count
        for row in self.traces:
            if row[9].startswith('fn_'):
                cinn_total_time += (t := row[1] - row[0])
                kernel_total_time[row[8]][0] += t
                kernel_total_time[row[8]][1] += 1
                if 'reduce' in row[9]:
                    reduce_total_time += t

        print('CINN Total Time (%%): %.2f' % (cinn_total_time / self.total_time * 100))
        print('Reduce Total Time (%%): %.2f' % (reduce_total_time / self.total_time * 100))
        print('Cum Time (%)\tTotal Time (%)\tAvg Time (us)\tReduce?\tKernel Name')

        kernel_total_time = sorted(kernel_total_time.items(), key=lambda i: -i[1][0])
        acc_ratio = 0
        for name, (t, cnt) in kernel_total_time[:100]:
            acc_ratio += (ratio := t / self.total_time)
            is_reduce = 'reduce' in name
            if (i := name.find('__COND')) != -1:
                name = name[:i]
            if len(name) > 60:
                name = f'[{name[:57]}...]({name})'
            print('%.2f\t%.2f\t%s\t%s\t%s' % (
                acc_ratio * 100, ratio * 100, add_comma(str(round(t / (cnt*1000)))),
                'Yes' if is_reduce else '', name
            ))

    def stat_occupancy_between(self, start, end):
        start, end = round(start * 1e9), round(end * 1e9)
        kernel_intervals = sorted(
            (row[0], row[1]) for row in self.traces
            if row[1] > start and row[0] < end)
        cur_end = start
        sum_time = 0
        for s, e in kernel_intervals:
            if e <= cur_end:
                continue
            if e >= end:
                sum_time += end - max(s, cur_end)
                break
            sum_time += e - max(s, cur_end)
            cur_end = e
        print('Inspecting (ns):', end - start)
        print('Occupied   (ns):', sum_time)
        print('Pipe Empty  (%):', (1 - sum_time / (end - start)) * 100)

def unmatch_cost(a):
    if a.startswith('volta_sgemm_'):
        return 100
    if a.startswith('volta_scudnn_'):
        return 1000
    return 1

def do_levenshtein_distance(max_n=10000):
    # We reverse the traces at the beginning to make the algorithm prefer
    # matching than insertion/deletion.
    a = [row[8] for row in reversed(rec0.traces[:max_n])]
    b = [row[8] for row in reversed(rec1.traces[:max_n])]

    m = [[0] * (len(b)+1) for _ in range(len(a)+1)]

    for i in range(len(a) + 1):
        m[i][0] = i
    for j in range(len(b) + 1):
        m[0][j] = j

    # Forward
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            if a[i-1] == b[j-1]:
                m[i][j] = m[i-1][j-1]
            else:
                m[i][j] = min(
                    m[i-1][j] + unmatch_cost(a[i-1]),
                    m[i][j-1] + unmatch_cost(b[j-1]),
                )
        if i % 100 == 0:
            print('\rfinished row: %d/%d' % (i, len(a)), end='', file=sys.stderr)

    print('\nmin_distance:', m[-1][-1], file=sys.stderr)

    # Traceback
    ans = []
    i, j = len(a), len(b)
    while i > 0 or j > 0:
        if j == 0:
            i -= 1
            ans.append((a[i], None))
        elif i == 0:
            j -= 1
            ans.append((None, b[j]))
        elif a[i-1] == b[j-1] and m[i-1][j-1] == m[i][j]:
            i -= 1
            j -= 1
            ans.append((a[i], b[j]))
        # Note: decrease i first to place cinn kernels after phi
        elif a[i-1] != b[j-1] and m[i-1][j] + unmatch_cost(a[i-1]) == m[i][j]:
            i -= 1
            ans.append((a[i], None))
        elif a[i-1] != b[j-1] and m[i][j-1] + unmatch_cost(b[j-1]) == m[i][j]:
            j -= 1
            ans.append((None, b[j]))
        else:
            print(a[i-1])
            print(b[j-1])
            print(m[i][j], m[i-1][j-1])
            print(m[i-1][j], unmatch_cost(a[i-1]))
            print(m[i][j-1], unmatch_cost(b[j-1]))
            raise Exception('bad position: %d, %d' % (i, j))

    return ans

def compare_by_levenshtein_dist():
    ans = do_levenshtein_distance()

    iter0 = iter(rec0.traces)
    iter1 = iter(rec1.traces)

    for a, b in ans:
        if a is None:
            row1 = next(iter1)
            print('', '', ' ', row1[8], row1[1]-row1[0], sep='\t')
        elif b is None:
            row0 = next(iter0)
            print(row0[1]-row0[0], row0[8], ' ', '', '', sep='\t')
        else:
            row0 = next(iter0)
            row1 = next(iter1)
            print(row0[1]-row0[0], row0[8], ' ', row1[8], row1[1]-row1[0], sep='\t')

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('''USAGE:
  parse_nsys_stats.py <a.sqlite>             : print stats of a.sqlite
  parse_nsys_stats.py <a.sqlite> <123> <789> : stat occupancy of a.sqlite from 123s to 789s''')
        exit()

    if len(sys.argv) == 3:
        rec = KernelTrace(sys.argv[1], sys.argv[2])
        # rec.print_cutlass_stats()
        exit()

    if len(sys.argv) == 4:
        rec = KernelTrace(sys.argv[1])
        rec.stat_occupancy_between(float(sys.argv[2]), float(sys.argv[3]))
        exit()

    #compare_by_levenshtein_dist()
