# create a diff of two schedule graphs
import difflib #, ocdiff
from collections import defaultdict
from typing import DefaultDict, List, Set, Tuple
from tinygrad.engine.schedule import ScheduleItem
from tinygrad.helpers import Context, colored
from tinygrad.lazy import LazyBuffer
from tinygrad.ops import LazyOp
from tinygrad.engine.realize import lower_schedule_item

def diff_schedule(s):
  si_for_buf: DefaultDict[LazyBuffer, List[ScheduleItem]] = defaultdict(list)
  for _,prescheduled in s:
    for ps in prescheduled.values():
      for buf in ps.outputs: si_for_buf[buf].append(ScheduleItem(ps.ast, tuple(x.buffer for x in ps.outputs+ps.inputs if x.size != 0), ps.metadata))
  changed = 0
  seen_diff: Set[Tuple[LazyOp, LazyOp]] = set()
  for buf, si in si_for_buf.items():
    asts = [x.ast for x in si]
    if len(set(asts)) == 1: continue
    if (asts[0], asts[1]) in seen_diff: continue
    seen_diff.add((asts[0], asts[1]))
    changed += 1
    #print(ocdiff.console_diff(render(ast[0]), render(ast[1])))
    ei0 = lower_schedule_item(si[0])
    ei1 = lower_schedule_item(si[1])
    diff = list(difflib.unified_diff(ei0.prg.p.src.splitlines(), ei1.prg.p.src.splitlines()))
    unified_diff = "\n".join(colored(line, "red" if line.startswith("-") else "green" if line.startswith("+") else None) for line in diff)
    print(unified_diff)
    with Context(DEBUG=2):
      tm0 = ei0.run(wait=True)
      tm1 = ei1.run(wait=True)
    assert tm0 is not None and tm1 is not None
    tm_diff = ((tm0 - tm1) / tm0) * 100
    if tm_diff > 0: print(colored(f"{tm_diff:.2f}% faster", "green"))
    else: print(colored(f"{tm_diff:,.2f}% slower", "red"))
  print(f"{changed} unique kernel{'s' if changed>1 else ''} changed")
