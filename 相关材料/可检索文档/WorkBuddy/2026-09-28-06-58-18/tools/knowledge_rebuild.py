# -*- coding: utf-8 -*-
"""Read-only source audit and deterministic knowledge projections. Explicit paths only."""
import pathlib,sqlite3,json,re,hashlib,datetime,collections,argparse,yaml,urllib.parse
VERSION='2026-10-13-v1'
SENSITIVE=re.compile('证件|医疗|症状|病理|密钥|密码|凭据')
PROTECT=re.compile('汇报|材料盘点|当前主线|今日卡|每日简报|自我理解引擎|🏠主页')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def ro(path):
    path=pathlib.Path(path);wal=pathlib.Path(str(path)+'-wal')
    if wal.exists() and wal.stat().st_size:
        raise RuntimeError('Nonempty WAL: acquire a consistent read snapshot before rebuilding: '+str(path))
    c=sqlite3.connect(path.as_uri()+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row;c.execute('pragma query_only=on');return c
def fm(text):
    m=re.match(r'\A\ufeff?---\r?\n(.*?)\r?\n---',text,re.S)
    if not m:return {},'missing'
    try:
        value=yaml.safe_load(m[1]+'\n');return (value or {},'ok') if isinstance(value,dict) or value is None else ({},'invalid_mapping')
    except yaml.YAMLError:return {},'invalid_yaml'
def link(path,label=None):
    path=str(path).replace('\\','/')
    if '[' in path or ']' in path:
        label=(label or pathlib.PurePosixPath(path).stem).replace('[','［').replace(']','］')
        return '['+label+']('+urllib.parse.quote('../'+path,safe='/')+')'
    return '[['+path.removesuffix('.md')+('|' +label.replace('|','/') if label else '')+']]'
def safe(s):return str(s or '').replace('|','／').replace('\n',' ').replace('\r',' ')
def write(path,text):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf8')
def note(title,body,extra=None):
    props={'type':'多维导航','generated_by':'knowledge_rebuild.py','schema_version':1,'source_audit_version':VERSION}
    props.update(extra or {})
    return '---\n'+yaml.safe_dump(props,allow_unicode=True,sort_keys=False)+'---\n\n# '+title+'\n\n'+body+'\n'
def build(vault,analysis,index,out):
    vault=pathlib.Path(vault);out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=True)
    a=ro(analysis);idx=ro(index)
    tables=[r[0] for r in a.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%'")]
    counts={t:a.execute('select count(*) from '+t).fetchone()[0] for t in tables}
    events={r['event_id']:dict(r) for r in a.execute('select * from events')}
    evidence=[dict(r) for r in a.execute('select * from evidence')]
    msgids=sorted({r['msg_id'] for r in evidence if r['msg_id'] is not None});messages={}
    for i in range(0,len(msgids),400):
        chunk=msgids[i:i+400]
        for r in idx.execute('select id,session_key,role,ts,content from messages where id in ('+','.join('?' for _ in chunk)+')',chunk):messages[r['id']]=dict(r)
    idx.close()
    audits=[];per_event=collections.defaultdict(list)
    for e in evidence:
        m=messages.get(e['msg_id']);ev=events.get(e['event_id'],{});reason=[]
        if e['msg_id'] is None:status='无消息定位'
        elif m is None:status='消息ID未找到'
        else:
            if e['session_key'] and e['session_key']!=m['session_key']:reason.append('会话不一致')
            if m['role']=='system' or re.search('撤回了一条消息|你已添加了|开启了朋友验证',m['content'] or ''):reason.append('系统提示不能支持事件细节')
            try:
                md=datetime.datetime.fromtimestamp(m['ts'],datetime.timezone(datetime.timedelta(hours=8))).date()
                if ev.get('date') and abs((md-datetime.date.fromisoformat(ev['date'][:10])).days)>1:reason.append('消息日期与事件日期相差超过1天')
            except (ValueError,TypeError,OverflowError):reason.append('日期不可比较')
            status='需优先复核' if reason else '定位可回查，语义未核验'
        row={'evidence_id':e['evidence_id'],'event_id':e['event_id'],'msg_id':e['msg_id'],'legacy_link_status':e['link_status'],'audit_status':status,'reasons':reason,'semantic_support':'未核验'}
        audits.append(row);per_event[e['event_id']].append(row)
    audit_events={}
    for eid in events:
        rs=per_event[eid];cnt=collections.Counter(r['audit_status'] for r in rs)
        summary='；'.join(k+':'+str(v) for k,v in sorted(cnt.items())) or '没有证据条目'
        audit_events[eid]={'summary':summary,'priority_review':any(r['reasons'] for r in rs),'raw_lookup_available':any(r['audit_status']=='定位可回查，语义未核验' for r in rs)}
    source_ids={r[0] for r in a.execute('select source_id from sources')}
    claim_evidence=[dict(r) for r in a.execute('select * from claim_evidence')]
    missing_sources=sorted({str(r['source_id']) for r in claim_evidence if r['source_id'] and r['source_id'] not in source_ids})
    audit={'version':VERSION,'counts':dict(collections.Counter(r['audit_status'] for r in audits)),'events':audit_events,'evidence':audits,'missing_claim_source_ids':missing_sources}
    write(out/'evidence_audit.json',json.dumps(audit,ensure_ascii=False,indent=2))
    # Original notes are indexed without altering their content or inventing semantic metadata.
    files=[p for p in vault.rglob('*') if p.is_file() and not any(s in ('.obsidian','.git','.trash','08_多维导航') for s in p.relative_to(vault).parts)]
    paths={p.relative_to(vault).as_posix():p for p in files};stem=collections.defaultdict(list)
    for r,p in paths.items():stem[p.stem].append(r)
    nodes=[];rawtexts={};ids={};protected=[]
    for r,p in paths.items():
        if p.suffix!='.md':continue
        excluded=bool(SENSITIVE.search(r));text='' if excluded else p.read_text(encoding='utf-8-sig');meta,state=fm(text) if not excluded else ({},'sensitive_excluded')
        isprotect=excluded or bool(PROTECT.search(r)) or r.startswith(('06_自我模型/','07_决策中枢/')) or bool(re.search('汇报|开题',text))
        if isprotect:protected.append(r)
        obj=meta.get('id');obj=str(obj) if obj is not None else None
        if obj:
            if obj in ids:raise ValueError('Duplicate ID '+obj)
            ids[obj]=r
        nodes.append({'path':r,'note_key':'NOTE-'+hashlib.sha256(r.encode()).hexdigest()[:16],'object_id':obj,'sha256':digest(p),'bytes':p.stat().st_size,'metadata_state':state,'type':str(meta.get('type','')),'status':str(meta.get('status','')),'as_of':str(meta.get('as_of',meta.get('updated',''))),'excluded':excluded,'protected':isprotect,'headings':re.findall(r'^#{1,3}\s+(.+)$',text,re.M)[:10]})
        if not excluded:rawtexts[r]=text
    relations=[];unresolved=[];tasks=[]
    for r,text in rawtexts.items():
        clean=re.sub(r'^```[^\n]*\n.*?^```\s*$', '',text,flags=re.M|re.S);clean=re.sub(r'`[^`\n]+`','',clean)
        for m in re.finditer(r'\[\[([^\]\n]+)\]\]',clean):
            target=m[1].split('|')[0].rstrip('\\').split('#')[0].replace('\\','/');found=None
            if not target:found=r
            elif target in paths:found=target
            elif target+'.md' in paths:found=target+'.md'
            elif target in ids:found=ids[target]
            else:
                name=pathlib.PurePosixPath(target).name
                exact=[v for v in paths if pathlib.PurePosixPath(v).name==name]
                if len(exact)==1:found=exact[0]
                candidates=stem.get(name.removesuffix('.md'),[])
                md=[v for v in candidates if v.endswith('.md')]
                if len(md)==1:found=md[0]
            if found:relations.append({'source':r,'target':found,'relation':'原有链接','verified_semantics':False})
            else:unresolved.append({'source':r,'target':target,'kind':'wiki'})
        for line in text.splitlines():
            if re.match(r'\s*[-*]\s*\[ \]',line) or '⬜' in line:
                tasks.append({'source':r,'source_hash':digest(paths[r]),'marker':'历史待办标记','confirmed_current':False})
    # A deterministic local registry stores metadata, edges and provenance, not duplicated raw chats.
    registry=out/'knowledge_index.sqlite'
    if registry.exists():registry.unlink() # only this derived file under explicit output directory
    c=sqlite3.connect(registry)
    c.executescript('create table notes(path text primary key,note_key text,object_id text,sha256 text,metadata_state text,type text,status text,as_of text,excluded int,protected int);create table links(source text,target text,relation text);create table event_index(event_id text primary key,date text,level text,person text,nature text,audit_summary text,existing_note text);create table evidence_audit(evidence_id integer,event_id text,msg_id integer,lookup_state text,reasons text,semantic_support text);create table rec_edges(rec_id text,claim_id text,dep_kind text);')
    c.executemany('insert into notes values(?,?,?,?,?,?,?,?,?,?)',[(n['path'],n['note_key'],n['object_id'],n['sha256'],n['metadata_state'],n['type'],n['status'],n['as_of'],n['excluded'],n['protected']) for n in nodes])
    c.executemany('insert into links values(?,?,?)',[(e['source'],e['target'],e['relation']) for e in relations])
    c.executemany('insert into event_index values(?,?,?,?,?,?,?)',[(eid,e.get('date'),e.get('level'),e.get('person'),e.get('nature'),audit_events[eid]['summary'],ids.get(eid)) for eid,e in sorted(events.items())])
    c.executemany('insert into evidence_audit values(?,?,?,?,?,?)',[(e['evidence_id'],e['event_id'],e['msg_id'],e['audit_status'],'；'.join(e['reasons']),e['semantic_support']) for e in audits])
    deps=[dict(r) for r in a.execute('select * from rec_deps')];c.executemany('insert into rec_edges values(?,?,?)',[(e['rec_id'],e['claim_id'],e['dep_kind']) for e in deps]);c.commit();assert c.execute('pragma integrity_check').fetchone()[0]=='ok';c.close()
    nav=vault/'08_多维导航';nav.mkdir(exist_ok=True)
    # Keep projections navigable without mutating any underlying project/person page.
    projects=[n for n in nodes if n['path'].startswith('01_个人信息/项目/') and n['path'].count('/')==2]
    projectlines=[]
    for n in projects:
        r=n['path'];text=rawtexts.get(r,'');incoming=[e['source'] for e in relations if e['target']==r];outgoing=[e['target'] for e in relations if e['source']==r]
        pname=pathlib.PurePosixPath(r).stem
        body='来源：'+link(r)+'\n\n原页状态：'+safe(n['status'])+'。这是原页记载，不代表今天已重新核实。\n\n'
        body+='## 资料与关联\n\n'+('\n'.join('- '+link(x) for x in sorted(set(outgoing))) or '暂无可解析出链。')+'\n\n## 哪些笔记使用它\n\n'+('\n'.join('- '+link(x) for x in sorted(set(incoming))) or '暂无可解析入链。')
        body+='\n\n## 调度边界\n\n'+('此项目含汇报活跃材料，仅提供原页入口，不重写内容或状态。' if n['protected'] else '期限、优先级、精力和完成状态未由本次自动推断。需要本人确认后建立独立行动记录。')
        fn='项目/'+pname+'.md';write(nav/fn,note(pname,body,{'type':'导航项目','source_note':link(r),'original_status':n['status'],'protected_source':n['protected'],'relation_count':len(set(incoming+outgoing))}))
        projectlines.append('- '+link('08_多维导航/'+fn)+' — '+safe(n['status']))
    write(nav/'01_项目入口.md',note('项目入口','\n'.join(projectlines)))
    people=[n for n in nodes if n['path'].startswith('03_微信聊天分析/01_人物档案/')]
    write(nav/'02_人物与专题入口.md',note('人物与专题入口','此目录混有基础档案、专题、报告和索引，不能把篇数当人数。原有推断没有被本次升级为事实。\n\n'+'\n'.join('- '+link(n['path']) for n in people if not n['excluded'])))
    # Every event is indexed; narrative duplication is deliberately avoided.
    months=collections.defaultdict(list)
    for eid,e in sorted(events.items()):months[(e.get('date') or '未知日期')[:7]].append((eid,e))
    for month,rows in sorted(months.items()):
        body='历史数据库记录；状态和摘要不是本轮事实核验。敏感细节不复制。ID可在本地knowledge_index.sqlite查来源状态。\n\n| 事件ID | 日期 | 级别 | 原记性质 | 来源审计 | 原笔记 |\n|---|---|---|---|---|---|\n'
        for eid,e in rows:body+='| '+ ' | '.join([eid,safe(e.get('date')),safe(e.get('level')),safe(e.get('nature')),safe(audit_events[eid]['summary']),link(ids[eid],eid) if eid in ids else '仅数据库记录；未伪造笔记'])+' |\n'
        write(nav/('时间/'+month+'.md'),note(month+'事件索引',body,{'event_month':month,'event_count':len(rows)}))
    write(nav/'03_时间入口.md',note('时间入口','全部'+str(len(events))+'个事件按原始事件日期分组；不以文件修改日期替代。\n\n'+'\n'.join('- '+link('08_多维导航/时间/'+m+'.md')+'：'+str(len(rows))+'条' for m,rows in sorted(months.items()))))
    body='原文定位与论断支持分开。以下只标机器可核验的定位问题；没有把“可回查”当语义支持。\n\n| 来源审计状态 | 条数 |\n|---|---:|\n'+'\n'.join('| '+k+' | '+str(v)+' |' for k,v in sorted(audit['counts'].items()))
    body+='\n\n## 需优先复核的事件\n\n| ID | 定位风险 | 原笔记 |\n|---|---|---|\n'
    for eid,r in sorted(audit_events.items()):
        if r['priority_review']:body+='| '+eid+' | '+safe(r['summary'])+' | '+(link(ids[eid],eid) if eid in ids else '数据库事件')+' |\n'
    body+='\n\n## 理解来源缺口\n\n来源表不存在的被引用ID：'+(', '.join(missing_sources) or '无')+'。本次未虚构补写来源。详细逐证据审计存于本地派生目录。'
    write(nav/'04_证据核验.md',note('证据核验',body))
    taskcounts=collections.Counter(t['source'] for t in tasks)
    write(nav/'05_行动与资源复核.md',note('行动与资源复核','原始待办标记共'+str(len(tasks))+'处，含重复、历史和示例，不等于现实未完成任务。\n\n现有人工入口：'+link('04_工作台/当前任务.md')+'。不自动填写成本、精力、期限或已完成状态。\n\n| 来源页 | 标记数 | 本次处理 |\n|---|---:|---|\n'+'\n'.join('| '+link(r)+' | '+str(n)+' | 待本人确认；不自动升级为当前行动 |' for r,n in sorted(taskcounts.items()) if not SENSITIVE.search(r))))
    claims={r['claim_id']:dict(r) for r in a.execute('select * from self_claims')};recs=[dict(r) for r in a.execute('select * from recommendations')]
    body='此处展示既有依赖，不自动认可旧理解；原始理由与系统推断仍需区分。\n\n'
    for rec in recs:
        body+='## '+safe(rec['rec_id'])+'\n\n'+safe(rec['title'])+'\n\n| 理解ID | 库内认识状态 | 本人复核 | 依赖性质 |\n|---|---|---|---|\n'
        for d in deps:
            if d['rec_id']==rec['rec_id']:
                q=claims.get(d['claim_id'],{});body+='| '+' | '.join(map(safe,[d['claim_id'],q.get('epistemic_status','缺失对象'),q.get('human_review'),d.get('dep_kind')]))+' |\n'
    body+='\n详见'+link('06_自我模型/建议与依赖链.md')+'。生产action_outcomes当前'+str(counts.get('action_outcomes',0))+'条；未制造反馈。'
    write(nav/'06_判断与建议依赖.md',note('判断与建议依赖',body))
    coverage={'version':VERSION,'original_files':len(files),'markdown':len(nodes),'scanned':len(rawtexts),'excluded':sum(n['excluded'] for n in nodes),'protected_count':len(protected),'database_counts':counts,'event_count':len(events),'evidence_count':len(evidence),'note_links':len(relations),'unresolved_wiki':len(unresolved),'task_marker_count':len(tasks),'projects':len(projects),'people_directory_notes':len(people),'audit_counts':audit['counts'],'missing_claim_source_ids':missing_sources}
    write(out/'coverage.json',json.dumps(coverage,ensure_ascii=False,indent=2));write(out/'notes.json',json.dumps(nodes,ensure_ascii=False,indent=2));write(out/'protected.json',json.dumps(protected,ensure_ascii=False,indent=2));write(out/'unresolved.json',json.dumps(unresolved,ensure_ascii=False,indent=2))
    write(nav/'07_覆盖与维护.md',note('覆盖与维护','本次全量是“结构索引与来源定位审计”，不是逐条事实已获证实。\n\n'+ '\n'.join('- '+k+'：'+str(v) for k,v in coverage.items() if isinstance(v,(int,str)))+'\n\n保护页与敏感页保留原文；无凭据读取。没有安装插件或后台任务。\n\n可重建命令：`python tools/knowledge_rebuild.py --vault <库路径> --analysis <分析库路径> --index <索引库路径> --output <派生目录>`。需要空间与并发检查；该命令只写导航与派生索引，不写原始分析数据库。\n\nBase语法参考：https://help.obsidian.md/bases/syntax 。已检查YAML及谓词逻辑；实际应用界面仍需打开验收。'))
    views=[]
    for name,expr,columns in [('项目','type == "导航项目"',['file.name','source_note','original_status','protected_source','relation_count']),('人物与专题','file.inFolder("03_微信聊天分析/01_人物档案")',['file.name','role','messages','updated']),('事件','type == "事件"',['file.name','id','date','person','source_audit','support_review']),('结论','type == "结论"',['file.name','id','status','verdict','has_counter','link_method']),('独立行动','type == "行动"',['file.name','action_state','due','priority','effort_minutes','energy_required']),('备考','file.inFolder("05_公考备考")',['file.name','status','updated']),('来源问题','support_review == "待核验"',['file.name','id','source_audit']),('资料附件','file.inFolder("03_微信聊天分析/_附件")',['file.name','file.ext','file.size'])]:views.append({'type':'table','name':name,'filters':{'and':[expr]},'order':columns})
    write(nav/'多维工作台.base',yaml.safe_dump({'views':views},allow_unicode=True,sort_keys=False))
    home='可按项目、人物、时间、证据、行动与依赖进入同一批资料。原页、原ID、历史判断保留，未知仍为未知。\n\n'
    for title in ['01_项目入口','02_人物与专题入口','03_时间入口','04_证据核验','05_行动与资源复核','06_判断与建议依赖','07_覆盖与维护']:home+='- '+link('08_多维导航/'+title+'.md')+'\n'
    home+='\n原生表格：'+link('08_多维导航/多维工作台.base')+'\n\n## 当前重点\n\n- “定位成功”不是“支持论断”：先看证据核验，再看推断。\n- 历史计划不是今天任务：行动先核实结果和期限。\n- 正在做的汇报及相关页面保留，不自动更新其状态。\n- 反馈需显式案例ID：不再套用固定财务案例。\n'
    for extra in ['08_来源补链与口径复核','09_校友会证据闭环示例','10_跨项目实践与验证入口']:
        if (nav/(extra+'.md')).exists():home+='\n- '+link('08_多维导航/'+extra+'.md')+'\n'
    write(nav/'00_多维总览.md',note('多维知识与行动入口',home))
    a.close();return coverage
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--vault',required=True);p.add_argument('--analysis',required=True);p.add_argument('--index',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    print(json.dumps(build(a.vault,a.analysis,a.index,a.output),ensure_ascii=False))

