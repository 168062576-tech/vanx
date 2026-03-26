// ===== STATE =====
const S={world:'world_alpha',agents:[],events:[],evFlt:'all',prev:null,occChart:null,trendChart:null,loading:false,activeRegion:null,roseChart:null};

const OCC_CLR={'农业':'#8B4513','制造业':'#708090','服务业':'#FF69B4','信息技术':'#4169E1','医疗':'#DC143C','教育':'#228B22','金融':'#DAA520','政府':'#9932CC','其他':'#808080'};
const REG_CFG={
    '商业区':{color:'rgba(78,205,196,.25)',bdr:'#4ECDC4',x:30,y:0,w:40,h:40},
    '住宅区':{color:'rgba(255,107,107,.25)',bdr:'#FF6B6B',x:0,y:0,w:30,h:50},
    '工业区':{color:'rgba(255,230,109,.2)',bdr:'#FFE66D',x:0,y:50,w:40,h:50},
    '教育区':{color:'rgba(149,225,211,.25)',bdr:'#95E1D3',x:70,y:0,w:30,h:35},
    '医疗区':{color:'rgba(243,129,129,.25)',bdr:'#F38181',x:70,y:35,w:30,h:30},
    '郊区':{color:'rgba(252,186,211,.2)',bdr:'#FCBAD3',x:40,y:65,w:60,h:35}
};
const EV_ICO={'birth':'👶','death':'💀','marriage':'🎉','job':'💼','epidemic':'🦠','house':'🏠','crime':'🚨','health':'🏥','misc':'📌'};

document.addEventListener('DOMContentLoaded',()=>{initTrend();loadAll();connectSSE();setInterval(()=>{loadStats();loadTrends()},5000);setTimeout(loadSocialNetwork,2000);setTimeout(loadMBTIDist,3000)});

// ===== SSE =====
let _evtSource=null;
function connectSSE(){
    if(_evtSource){_evtSource.close();_evtSource=null}
    try{
        _evtSource=new EventSource('/api/events/stream?world='+S.world);
        _evtSource.onopen=()=>{const dot=document.getElementById('sse-dot');if(dot){dot.className='sse-status connected';dot.title='SSE connected'}};
        _evtSource.onmessage=(e)=>{try{const ev=JSON.parse(e.data);ev._new=true;S.events.unshift(ev);if(S.events.length>200)S.events.pop();renderEv()}catch(err){}};
        _evtSource.onerror=()=>{const dot=document.getElementById('sse-dot');if(dot){dot.className='sse-status disconnected';dot.title='SSE disconnected'}
            setTimeout(()=>{if(_evtSource&&_evtSource.readyState===2){_evtSource.close();_evtSource=null;setInterval(loadEvents,5000)}},15000)};
    }catch(err){setInterval(loadEvents,5000)}
}

function switchWorld(){S.world=document.getElementById('wsel').value;S.prev=null;connectSSE();loadAll()}

async function loadAll(){
    if(S.loading)return;S.loading=true;
    try{await Promise.all([loadStats(),loadAgents(),loadEvents(),loadTrends(),loadPyramid(),loadSocialNetwork(),loadMBTIDist()])}
    catch(e){console.error(e)}
    finally{S.loading=false}
}

async function loadStats(){
    try{
        const r=await fetch('/api/stats?world='+S.world);const d=await r.json();
        const raw=d.data||d;
        if(raw.error)return;
        // Transform API format (demographics/economy/social/simulation) to frontend format
        const stats={
            population: raw.simulation?.total_agents || raw.population || 0,
            employment_rate: raw.economy ? Math.round((1 - raw.economy.unemployment_rate) * 100 * 10) / 10 : (raw.employment_rate || 0),
            avg_income: raw.economy?.avg_income || raw.avg_income || 0,
            avg_satisfaction: raw.social?.avg_happiness ? raw.social.avg_happiness / 20 : (raw.avg_satisfaction || 3),
            time: raw.time || {year: 2026, day: 1},
            statistics: raw.statistics || {},
            occupation: raw.occupation || {},
            region: raw.region || {},
        };
        // Build occupation/region stats from loaded agents if not in API response
        if(Object.keys(stats.occupation).length===0 && S.agents.length>0){
            S.agents.forEach(a=>{
                const o=a.occupation||'待业';stats.occupation[o]=(stats.occupation[o]||0)+1;
                const r=a.region||'住宅区';stats.region[r]=(stats.region[r]||0)+1;
            });
        }
        renderKPI(stats);renderStats(stats);renderLeg(stats);renderPie(stats.occupation);S.prev=stats;
    }catch(e){console.warn('stats err',e)}
}

async function loadAgents(){
    try{
        // Try display API first (has Chinese names + region coords)
        let agents=[];
        try{
            const r=await fetch('/api/agents/display?limit=2000');
            if(r.ok){const d=await r.json();if(d.success)agents=d.data?.agents||d.agents||[];}
        }catch(_){}
        // Fallback to basic agents API
        if(!agents.length){
            const r=await fetch('/api/agents?world='+S.world);const d=await r.json();
            agents=d.data?.agents||d.agents||[];
        }
        S.agents=agents;
        document.getElementById('ac-lbl').textContent=S.agents.length+' agents';
        renderMap(S.agents);
    }catch(e){console.warn('agents err',e)}
}

async function loadEvents(){
    try{
        const r=await fetch('/api/events?limit=40&world='+S.world);
        if(!r.ok){mockEvents();return}
        const d=await r.json();S.events=d.events||(d.data&&d.data.events)||[];renderEv();
    }catch(e){mockEvents()}
}

async function loadTrends(){
    try{
        const r=await fetch('/api/trends?world='+S.world);
        if(!r.ok){mockTrend();return}
        const d=await r.json();renderTrend(d);
    }catch(e){mockTrend()}
}

// ===== KPI =====
function renderKPI(d){
    const p=S.prev;
    setK('k-pop',d.population.toLocaleString(),'kd-pop',p?.population,d.population);
    setK('k-emp',d.employment_rate+'%','kd-emp',p?.employment_rate,d.employment_rate);
    setK('k-inc','$'+Math.round(d.avg_income).toLocaleString(),'kd-inc',p?.avg_income,d.avg_income);
    setK('k-sat',d.avg_satisfaction.toFixed(2),'kd-sat',p?.avg_satisfaction,d.avg_satisfaction);
    const t=d.time||{};
    document.getElementById('htime').textContent='📅 '+((t.year||2026))+'年 第'+(t.day||1)+'天 | '+new Date().toLocaleTimeString();
}
function setK(vid,txt,did,pv,cv){
    document.getElementById(vid).textContent=txt;
    const el=document.getElementById(did);
    if(pv!=null&&pv!==cv){const df=cv-pv;const a=df>0?'▲':'▼';el.className='kpi-delta '+(df>0?'up':'down');el.textContent=a+' '+(Math.abs(df)<1?df.toFixed(2):Math.round(df).toLocaleString())}
}

// ===== Stats Panel =====
function renderStats(d){
    const s=d.statistics||{};
    document.getElementById('stats-c').innerHTML=`
        <div class="stat-item"><span class="stat-label">世界时间</span><span class="stat-val">${(d.time?.year||2026)}年${(d.time?.day||1)}天</span></div>
        <div class="stat-item"><span class="stat-label">总出生</span><span class="stat-val">${(s.total_births||0).toLocaleString()}</span></div>
        <div class="stat-item"><span class="stat-label">总死亡</span><span class="stat-val">${(s.total_deaths||0).toLocaleString()}</span></div>
        <div class="stat-item"><span class="stat-label">总结婚</span><span class="stat-val">${(s.total_marriages||0).toLocaleString()}</span></div>`;
}

// ===== Legends =====
function renderLeg(d){
    let rh='';for(const[r,c]of Object.entries(d.region||{})){const cfg=REG_CFG[r];rh+=`<div class="leg-item"><div class="leg-dot" style="background:${cfg?cfg.bdr:'#888'}"></div><span>${r}</span><span class="leg-cnt">${c}</span></div>`}
    document.getElementById('reg-leg').innerHTML=rh;
    let oh='';for(const[o,c]of Object.entries(d.occupation||{})){oh+=`<div class="leg-item"><div class="leg-dot" style="background:${OCC_CLR[o]||'#888'}"></div><span>${o}</span><span class="leg-cnt">${c}</span></div>`}
    document.getElementById('occ-leg').innerHTML=oh;
}

// ===== Pie =====
function renderPie(occ){
    if(!occ)return;
    const dom=document.getElementById('occ-chart');if(!dom)return;
    if(!S.roseChart){S.roseChart=echarts.init(dom,null,{renderer:'canvas'});window.addEventListener('resize',()=>{if(S.roseChart)S.roseChart.resize()})}
    const data=Object.entries(occ).map(([name,value])=>({name,value,itemStyle:{color:OCC_CLR[name]||'#888'}}));
    S.roseChart.setOption({backgroundColor:'transparent',tooltip:{trigger:'item',backgroundColor:'rgba(22,33,62,.95)',borderColor:'rgba(102,126,234,.4)',textStyle:{color:'#edf2f7',fontSize:11},formatter:'{b}: {c} ({d}%)'},
        series:[{type:'pie',roseType:'area',radius:['15%','75%'],center:['50%','52%'],data:data,label:{color:'#a0aec0',fontSize:10,formatter:'{b}'},labelLine:{lineStyle:{color:'rgba(160,174,192,.3)'}},itemStyle:{borderRadius:4,borderColor:'rgba(15,14,23,.6)',borderWidth:2},emphasis:{itemStyle:{shadowBlur:12,shadowColor:'rgba(0,0,0,.3)'}},animationType:'scale',animationEasing:'elasticOut',animationDuration:800}]
    },true);
}

// ===== Population Pyramid =====
let _pyramidChart=null;
async function loadPyramid(){
    try{
        const r=await fetch('/api/stats/pyramid');if(!r.ok)return;
        const d=await r.json();if(d.success)renderPyramid(d.data);
    }catch(e){console.warn('pyramid err',e)}
}
function renderPyramid(d){
    const dom=document.getElementById('pyramid-chart');if(!dom)return;
    if(!_pyramidChart){_pyramidChart=echarts.init(dom,null,{renderer:'canvas'});window.addEventListener('resize',()=>{if(_pyramidChart)_pyramidChart.resize()})}
    const maleData=d.male.map(v=>-v);
    _pyramidChart.setOption({
        backgroundColor:'transparent',
        tooltip:{trigger:'axis',backgroundColor:'rgba(22,33,62,.95)',borderColor:'rgba(102,126,234,.4)',textStyle:{color:'#edf2f7',fontSize:11},
            formatter:function(params){let s=params[0].axisValue+'<br>';params.forEach(function(p){s+=p.marker+p.seriesName+': <b>'+Math.abs(p.value)+'</b><br>'});return s}},
        grid:{left:50,right:20,top:10,bottom:20},
        xAxis:{type:'value',axisLine:{show:false},axisLabel:{color:'#718096',fontSize:9,formatter:function(v){return Math.abs(v)}},splitLine:{lineStyle:{color:'rgba(102,126,234,.08)'}}},
        yAxis:{type:'category',data:d.age_groups,axisLine:{lineStyle:{color:'rgba(102,126,234,.3)'}},axisLabel:{color:'#a0aec0',fontSize:9},axisTick:{show:false}},
        series:[
            {name:'男性',type:'bar',stack:'pyramid',data:maleData,itemStyle:{color:'#4169E1',borderRadius:[4,0,0,4]},barWidth:'60%',emphasis:{itemStyle:{shadowBlur:6,shadowColor:'rgba(0,0,0,.2)'}}},
            {name:'女性',type:'bar',stack:'pyramid',data:d.female,itemStyle:{color:'#FF69B4',borderRadius:[0,4,4,0]},barWidth:'60%',emphasis:{itemStyle:{shadowBlur:6,shadowColor:'rgba(0,0,0,.2)'}}}
        ],
        animation:true,animationDuration:600,animationEasing:'cubicOut'
    },true);
}

// ===== Social Network Graph =====
let _networkChart=null;
async function loadSocialNetwork(){
    try{
        const limitSel=document.getElementById('network-limit');
        const limit=limitSel?parseInt(limitSel.value):100;
        const r=await fetch('/api/social/network?limit='+limit);
        if(!r.ok){
            // Try v1 API path
            const r2=await fetch('/api/v1/social/network?limit='+limit,{headers:{'X-API-Key':'yulong-dev-key'}});
            if(!r2.ok)return;
            const d2=await r2.json();
            if(d2.success)renderNetworkGraph(d2.data);
            return;
        }
        const d=await r.json();
        if(d.success)renderNetworkGraph(d.data);
    }catch(e){console.warn('social network err',e)}
}

function renderNetworkGraph(data){
    const dom=document.getElementById('network-chart');
    if(!dom)return;
    if(!_networkChart){
        _networkChart=echarts.init(dom,null,{renderer:'canvas'});
        window.addEventListener('resize',()=>{if(_networkChart)_networkChart.resize()});
    }

    // Build categories from occupation groups
    const groupSet=new Set();
    data.nodes.forEach(n=>groupSet.add(n.group));
    const groups=[...groupSet].sort();
    const categories=groups.map(g=>({name:g}));
    const groupIndex={};
    groups.forEach((g,i)=>{groupIndex[g]=i});

    // Map nodes
    const nodes=data.nodes.map(n=>{
        const clr=OCC_CLR[n.group]||OCC_CLR[n.occupation]||'#888';
        return {
            id:String(n.id),
            name:n.name,
            symbolSize:Math.max(8,Math.min(35,(n.value||1)*3+5)),
            category:groupIndex[n.group]||0,
            itemStyle:{color:clr,borderColor:'rgba(255,255,255,.2)',borderWidth:1},
            label:{show:n.value>=5,color:'#ddd',fontSize:9},
            tooltip:{formatter:function(){
                return '<b>'+n.name+'</b><br>'
                    +'职业: '+n.occupation+'<br>'
                    +'年龄: '+n.age+'岁<br>'
                    +'关系数: '+n.value;
            }},
            _raw:n
        };
    });

    // Link type styles
    const LINK_STYLES={
        spouse:{color:'#e84393',width:3,type:'solid',curveness:0.1},
        family:{color:'#fdcb6e',width:2,type:'solid',curveness:0.15},
        close_friend:{color:'#00cec9',width:1.5,type:'dashed',curveness:0.2},
        friend:{color:'rgba(160,174,192,.3)',width:1,type:'dashed',curveness:0.2},
        colleague:{color:'rgba(102,126,234,.3)',width:1,type:'dotted',curveness:0.15},
    };

    const links=data.links.map(l=>{
        const st=LINK_STYLES[l.type]||LINK_STYLES.friend;
        return {
            source:String(l.source),
            target:String(l.target),
            lineStyle:{color:st.color,width:st.width,type:st.type,curveness:st.curveness,opacity:0.6},
            _type:l.type
        };
    });

    _networkChart.setOption({
        backgroundColor:'transparent',
        tooltip:{
            trigger:'item',
            backgroundColor:'rgba(22,33,62,.95)',
            borderColor:'rgba(102,126,234,.4)',
            textStyle:{color:'#edf2f7',fontSize:11}
        },
        legend:[{
            data:categories.map(c=>c.name),
            textStyle:{color:'#a0aec0',fontSize:9},
            top:2,right:4,
            orient:'vertical',
            itemWidth:10,itemHeight:10,
            itemGap:4,
            formatter:function(name){return name.length>4?name.slice(0,4)+'…':name}
        }],
        series:[{
            type:'graph',
            layout:'force',
            data:nodes,
            links:links,
            categories:categories,
            roam:true,
            draggable:true,
            force:{
                repulsion:80,
                gravity:0.08,
                edgeLength:[40,120],
                layoutAnimation:true,
                friction:0.6
            },
            label:{show:false,position:'right',fontSize:9,color:'#ccc'},
            emphasis:{
                focus:'adjacency',
                label:{show:true,fontSize:11,color:'#fff'},
                lineStyle:{width:3,opacity:1}
            },
            animationDuration:1500,
            animationEasingUpdate:'quinticInOut'
        }]
    },true);

    // Click node → show agent detail
    _networkChart.off('click');
    _networkChart.on('click',function(params){
        if(params.dataType==='node'&&params.data._raw){
            const n=params.data._raw;
            showDetail({id:n.id,name:n.name,occupation:n.occupation,age:n.age,gender:n.gender,region:'',income:0});
        }
    });
}

// ===== Region Map =====
function renderMap(agents){
    const m=document.getElementById('region-map');m.innerHTML='';
    const ra={};for(const r of Object.keys(REG_CFG))ra[r]=[];
    agents.forEach(a=>{const r=a.region||'住宅区';if(!ra[r])ra[r]=[];ra[r].push(a)});

    for(const[name,cfg]of Object.entries(REG_CFG)){
        const b=document.createElement('div');b.className='reg-block';b.dataset.region=name;
        b.style.cssText=`left:${cfg.x}%;top:${cfg.y}%;width:${cfg.w}%;height:${cfg.h}%;background:${cfg.color};border:2px solid ${cfg.bdr}40;cursor:pointer`;
        const l=document.createElement('div');l.className='reg-lbl';l.textContent=name;b.appendChild(l);
        const c=document.createElement('div');c.className='reg-cnt';c.textContent=(ra[name]||[]).length+'人';b.appendChild(c);
        b.addEventListener('click',(ev)=>{ev.stopPropagation();toggleRegionPopup(name,b,ra[name]||[],cfg)});
        m.appendChild(b);

        (ra[name]||[]).forEach(a=>{
            const d=document.createElement('div');d.className='adot';
            d.style.left=a.x+'%';d.style.top=a.y+'%';
            d.style.background=OCC_CLR[a.occupation]||'#888';
            d._agentData=a;
            d.addEventListener('click',()=>showDetail(a));
            d.addEventListener('mouseenter',e=>showTT(e,a));
            d.addEventListener('mouseleave',hideTT);
            m.appendChild(d);
        });
    }
    populateFilters();
    filterAgents();
}

// ===== Search/Filter =====
function populateFilters(){
    const occSet=new Set(),regSet=new Set();
    S.agents.forEach(a=>{if(a.occupation)occSet.add(a.occupation);if(a.region)regSet.add(a.region)});
    const occSel=document.getElementById('filter-occ'),regSel=document.getElementById('filter-region');
    const curOcc=occSel.value,curReg=regSel.value;
    occSel.innerHTML='<option value="">全部职业</option>'+[...occSet].sort().map(o=>`<option value="${o}"${o===curOcc?' selected':''}>${o}</option>`).join('');
    regSel.innerHTML='<option value="">全部区域</option>'+[...regSet].sort().map(r=>`<option value="${r}"${r===curReg?' selected':''}>${r}</option>`).join('');
}
function filterAgents(){
    const q=(document.getElementById('agent-search').value||'').trim().toLowerCase();
    const occ=document.getElementById('filter-occ').value;
    const reg=document.getElementById('filter-region').value;
    const dots=document.querySelectorAll('.adot');
    let matchCount=0;const hasFilter=q||occ||reg;
    dots.forEach(dot=>{
        const a=dot._agentData;if(!a){dot.classList.remove('dimmed','highlighted');return}
        const match=(!q||a.name.toLowerCase().includes(q))&&(!occ||a.occupation===occ)&&(!reg||a.region===reg);
        if(!hasFilter){dot.classList.remove('dimmed','highlighted')}
        else if(match){dot.classList.remove('dimmed');dot.classList.add('highlighted');matchCount++}
        else{dot.classList.add('dimmed');dot.classList.remove('highlighted')}
    });
    const el=document.getElementById('search-cnt');
    el.textContent=hasFilter?matchCount+'/'+S.agents.length+' 匹配':'';
}

// ===== Region Popup =====
function toggleRegionPopup(regionName,blockEl,regionAgents,cfg){
    const oldPopup=document.querySelector('.region-popup');if(oldPopup)oldPopup.remove();
    const blocks=document.querySelectorAll('.reg-block');
    if(S.activeRegion===regionName){S.activeRegion=null;blocks.forEach(b=>{b.classList.remove('active','dimmed-region');b.style.borderWidth='2px'});return}
    S.activeRegion=regionName;
    blocks.forEach(b=>{
        if(b.dataset.region===regionName){b.classList.add('active');b.classList.remove('dimmed-region');b.style.borderWidth='3px';b.style.borderColor=cfg.bdr}
        else{b.classList.remove('active');b.classList.add('dimmed-region');b.style.borderWidth='2px'}
    });
    const n=Math.max(regionAgents.length,1);
    const avgInc=Math.round(regionAgents.reduce((s,a)=>s+(a.income||0),0)/n);
    const avgSat=(regionAgents.reduce((s,a)=>s+(a.satisfaction||3),0)/n).toFixed(2);
    const occCount={};regionAgents.forEach(a=>{const o=a.occupation||'其他';occCount[o]=(occCount[o]||0)+1});
    const topOcc=Object.entries(occCount).sort((a,b)=>b[1]-a[1]).slice(0,5);
    const icons={'商业区':'🏢','住宅区':'🏠','工业区':'🏭','教育区':'🎓','医疗区':'🏥','郊区':'🌾'};
    const popup=document.createElement('div');popup.className='region-popup';
    const mapEl=document.getElementById('region-map');
    const mapRect=mapEl.getBoundingClientRect();const blockRect=blockEl.getBoundingClientRect();
    let popLeft=blockRect.left-mapRect.left+blockRect.width/2;
    let popTop=blockRect.top-mapRect.top+blockRect.height+5;
    if(popLeft+220>mapEl.clientWidth)popLeft=mapEl.clientWidth-230;
    if(popLeft<0)popLeft=10;
    if(popTop+200>mapEl.clientHeight)popTop=blockRect.top-mapRect.top-210;
    popup.style.left=popLeft+'px';popup.style.top=popTop+'px';
    popup.innerHTML=`<button class="close-btn" onclick="this.parentElement.remove();resetRegionHighlight()">✕</button>
        <h3>${icons[regionName]||'📍'} ${regionName}</h3>
        <div class="rp-row"><span class="rp-label">人数</span><span class="rp-val">${regionAgents.length}</span></div>
        <div class="rp-row"><span class="rp-label">平均收入</span><span class="rp-val">$${avgInc.toLocaleString()}</span></div>
        <div class="rp-row"><span class="rp-label">满意度</span><span class="rp-val">${avgSat}</span></div>
        <div class="rp-occ"><div style="color:var(--muted);font-size:.85em;margin-bottom:4px">主要职业：</div>${topOcc.map(([o,c])=>`<div class="rp-occ-item"><span style="display:flex;align-items:center;gap:4px"><span style="width:6px;height:6px;border-radius:2px;background:${OCC_CLR[o]||'#888'}"></span>${o}</span><span>${c}</span></div>`).join('')}</div>`;
    mapEl.appendChild(popup);
}
function resetRegionHighlight(){S.activeRegion=null;document.querySelectorAll('.reg-block').forEach(b=>{b.classList.remove('active','dimmed-region');b.style.borderWidth='2px'})}

function showTT(e,a){const t=document.getElementById('mtt');document.getElementById('ttn').textContent=a.name+' ('+a.age+'岁)';document.getElementById('tti').textContent=a.occupation+' | '+a.region+' | $'+(a.income||0).toLocaleString()+'/月';t.style.display='block';t.style.left=(e.clientX+12)+'px';t.style.top=(e.clientY-10)+'px'}
function hideTT(){document.getElementById('mtt').style.display='none'}

// ===== Agent Detail =====
async function showDetail(ag){
    try{
        // Try display API (Chinese names)
        let a=ag, region=ag.region||'';
        try{
            const r=await fetch('/api/agents/'+ag.id+'/display');
            if(r.ok){const d=await r.json();if(d.success){a=d.data;region=a.region||region;}}
        }catch(_){}
        const clr=OCC_CLR[a.occupation]||'#667eea';
        let html=`
            <div class="agent-hdr"><div class="agent-av" style="background:${clr}30;color:${clr}">${a.gender==='男'?'👨':a.gender==='女'?'👩':'🧑'}</div>
            <div><div class="agent-name">${a.name}</div><span class="agent-tag" style="background:${clr}22;color:${clr}">${a.occupation}</span></div></div>
            <div class="d-row"><span class="lb">年龄</span><span class="vl">${a.age}岁</span></div>
            <div class="d-row"><span class="lb">性别</span><span class="vl">${a.gender}</span></div>
            <div class="d-row"><span class="lb">月收入</span><span class="vl">$${(a.income||a.income_monthly||0).toLocaleString()}</span></div>
            <div class="d-row"><span class="lb">教育</span><span class="vl">${a.education||'未知'}</span></div>
            <div class="d-row"><span class="lb">满意度</span><span class="vl">${(a.satisfaction||0).toFixed?.(2)||a.satisfaction} ⭐</span></div>
            <div class="d-row"><span class="lb">区域</span><span class="vl">${region}</span></div>`;

        // ── Tab 切换面板（Fix6: 解决1500px内容塞330px的问题） ──
        html+=`<div class="detail-tabs">
            <button class="dtab active" onclick="switchDetailTab('profile',this)">📋 档案</button>
            <button class="dtab" onclick="switchDetailTab('life',this)">💰 生活</button>
            <button class="dtab" onclick="switchDetailTab('chat',this)">💬 对话</button>
        </div>`;

        // Tab 1: 档案（能力+MBTI+技能+特质）
        html+=`<div id="dtab-profile" class="dtab-content" style="display:block">
            <div id="agent-abilities-panel"></div>
        </div>`;

        // Tab 2: 生活（金融+时间线+故事）
        html+=`<div id="dtab-life" class="dtab-content" style="display:none">
            <div id="agent-finance-panel"></div>
            <div id="agent-timeline-panel"></div>
            <div id="agent-story-panel"></div>
        </div>`;

        // Tab 3: 对话
        html+=`<div id="dtab-chat" class="dtab-content" style="display:none">
            <div class="agent-chat">
                <div class="agent-chat-title">💬 与居民对话</div>
                <div id="chat-messages" class="chat-messages"></div>
                <div class="chat-input-row">
                    <input id="chat-input" type="text" placeholder="和这位居民聊聊..." onkeypress="if(event.key==='Enter')sendChat(${ag.id})">
                    <button class="chat-send-btn" onclick="sendChat(${ag.id})">发送</button>
                </div>
            </div>
        </div>`;

        document.getElementById('agent-det').innerHTML=html;

        // ── 异步加载能力数据 ──
        loadAgentAbilities(ag.id);
        // ── 异步加载金融数据 ──
        loadAgentFinance(ag.id);
        // ── 异步加载时间线 ──
        loadAgentTimeline(ag.id);
        // ── 异步加载故事 ──
        loadAgentStory(ag.id);

    }catch(e){
        const a=ag;document.getElementById('agent-det').innerHTML=`
            <div class="agent-hdr"><div class="agent-av" style="background:rgba(102,126,234,.2)">🧑</div><div><div class="agent-name">${a.name}</div></div></div>
            <div class="d-row"><span class="lb">职业</span><span class="vl">${a.occupation}</span></div>
            <div class="d-row"><span class="lb">收入</span><span class="vl">$${(a.income||0).toLocaleString()}</span></div>`;
    }
}

// 异步加载 Agent 能力数据
async function loadAgentAbilities(agentId){
    const panel=document.getElementById('agent-abilities-panel');
    if(!panel)return;
    try{
        const r=await fetch('/api/v1/agents/'+agentId+'/abilities',{headers:{'X-API-Key':'yulong-dev-key'}});
        if(!r.ok)return;
        const d=await r.json();
        if(!d.success||!d.data||Object.keys(d.data).length===0)return;

        const profile=d.data;
        let html='';

        // MBTI 徽章
        if(profile.mbti){
            html+=`<div class="ability-section-title">🧠 MBTI 人格</div>`;
            html+=`<div style="margin:4px 0"><span class="mbti-badge mbti-${profile.mbti}">${profile.mbti}</span></div>`;
        }

        // 天赋雷达图
        if(profile.talents&&Object.keys(profile.talents).length>0){
            html+=`<div class="ability-section-title">⭐ 天赋</div>`;
            html+=`<div class="talent-radar" id="agent-talent-radar"></div>`;
        }

        // 技能列表
        if(profile.skills&&profile.skills.length>0){
            html+=`<div class="ability-section-title">🎯 技能</div>`;
            html+=`<div class="skill-bar-list">`;
            // 按 level 降序排列，最多显示 8 个
            const sortedSkills=profile.skills.slice().sort(function(a,b){return(b.level||0)-(a.level||0)}).slice(0,8);
            sortedSkills.forEach(function(sk){
                const tierClass=getSkillTierClass(sk.tier);
                const pct=Math.min(100,Math.max(1,sk.level||0));
                html+=`<div class="skill-bar">
                    <span class="skill-bar-name" title="${sk.name}">${sk.name}</span>
                    <div class="skill-bar-track"><div class="skill-bar-fill ${tierClass}" style="width:${pct}%"></div></div>
                    <span class="skill-bar-level">${(sk.level||0).toFixed(1)}</span>
                    <span class="skill-bar-tier ${tierClass}">${getSkillTierLabel(sk.tier)}</span>
                </div>`;
            });
            html+=`</div>`;
        }

        // 稀有特质
        if(profile.traits&&profile.traits.length>0){
            html+=`<div class="ability-section-title">✨ 特质</div>`;
            html+=`<div class="trait-tag-list">`;
            profile.traits.forEach(function(tr,i){
                const name=typeof tr==='string'?tr:(tr.name||'');
                const effect=typeof tr==='object'&&tr.effect?JSON.stringify(tr.effect):'';
                const tagClass=getTraitTagClass(i);
                html+=`<span class="trait-tag ${tagClass}" title="${effect}">✦ ${name}</span>`;
            });
            html+=`</div>`;
        }

        // 协同效应
        if(profile.synergies&&profile.synergies.length>0){
            html+=`<div class="ability-section-title">🔗 协同效应</div>`;
            html+=`<div class="synergy-list">`;
            profile.synergies.forEach(function(syn){
                const skills=(syn.skills||[]).join('+');
                const bonus=syn.bonus?'+'+Math.round(syn.bonus*100)+'%':'';
                html+=`<div class="synergy-item">
                    <span class="synergy-name">${syn.name||''}</span>
                    <span class="synergy-skills">${skills}</span>
                    <span class="synergy-bonus">${bonus}</span>
                </div>`;
            });
            html+=`</div>`;
        }

        panel.innerHTML=html;

        // 渲染天赋雷达图（DOM 已存在后）
        if(profile.talents&&Object.keys(profile.talents).length>0){
            setTimeout(function(){renderTalentRadar('agent-talent-radar',profile.talents)},50);
        }
    }catch(e){console.warn('loadAgentAbilities err',e)}
}

// 异步加载 Agent 金融数据
async function loadAgentFinance(agentId){
    const panel=document.getElementById('agent-finance-panel');
    if(!panel)return;
    try{
        const r=await fetch('/api/v1/agents/'+agentId+'/finance',{headers:{'X-API-Key':'yulong-dev-key'}});
        if(!r.ok)return;
        const d=await r.json();
        if(!d.success||!d.data||Object.keys(d.data).length===0)return;

        const fin=d.data;
        let html=`<div class="finance-summary">`;
        html+=`<div class="finance-summary-title">💰 金融概况</div>`;

        const rows=[
            {label:'月收入',key:'income',format:formatMoney},
            {label:'净资产',key:'net_worth',format:formatMoney,signed:true},
            {label:'储蓄',key:'savings',format:formatMoney},
            {label:'负债',key:'debt',format:formatMoney,negative:true},
            {label:'信用评分',key:'credit_score',format:function(v){return v?Math.round(v)+'分':'--'}},
            {label:'住房',key:'housing_status',format:function(v){
                const m={'owned':'自有','rented':'租房','homeless':'无房','mortgage':'按揭','public':'公租房'};
                return m[v]||v||'--';
            }},
            {label:'月支出',key:'monthly_expenses',format:formatMoney},
        ];

        rows.forEach(function(row){
            const val=fin[row.key];
            if(val===undefined||val===null||val===0&&row.key!=='debt')return;
            const formatted=row.format(val);
            let cls='';
            if(row.signed&&typeof val==='number')cls=val>=0?'positive':'negative';
            if(row.negative&&typeof val==='number'&&val>0)cls='negative';
            html+=`<div class="finance-row"><span class="finance-label">${row.label}</span><span class="finance-val ${cls}">${formatted}</span></div>`;
        });

        // 如果有额外字段（如投资组合等），也显示
        const knownKeys=new Set(['income','net_worth','savings','debt','credit_score','housing_status','monthly_expenses']);
        Object.keys(fin).forEach(function(k){
            if(knownKeys.has(k))return;
            const v=fin[k];
            if(v===undefined||v===null)return;
            const label=k.replace(/_/g,' ');
            const formatted=typeof v==='number'?formatMoney(v):String(v);
            html+=`<div class="finance-row"><span class="finance-label">${label}</span><span class="finance-val">${formatted}</span></div>`;
        });

        html+=`</div>`;
        panel.innerHTML=html;
    }catch(e){console.warn('loadAgentFinance err',e)}
}

// ===== Agent Timeline =====
async function loadAgentTimeline(agentId){
    const panel=document.getElementById('agent-timeline-panel');
    if(!panel)return;
    try{
        const r=await fetch('/api/v1/agents/'+agentId+'/timeline',{headers:{'X-API-Key':'yulong-dev-key'}});
        if(!r.ok)return;
        const d=await r.json();
        if(!d.success)return;
        const events=d.data.events||[];
        if(!events.length){panel.innerHTML='<div style="color:var(--muted);padding:10px;font-size:.82em">暂无事件记录</div>';return;}
        let html='<div class="ability-section-title">📜 生命时间线</div>';
        html+='<div class="timeline">';
        events.forEach(function(e){
            const color=getEventColor(e.type);
            html+=`<div class="tl-item">
                <div class="tl-dot" style="background:${color}"></div>
                <div class="tl-content">
                    <div class="tl-month">第${e.month||0}月</div>
                    <div class="tl-desc">${e.description||e.type}</div>
                </div>
            </div>`;
        });
        html+='</div>';
        panel.innerHTML=html;
    }catch(e){console.warn('loadAgentTimeline err',e)}
}

function getEventColor(type){
    const colors={
        'birth':'#00b894','career_change':'#fdcb6e','marriage':'#e84393',
        'divorce':'#d63031','retirement':'#636e72','crime':'#e17055',
        'skill':'#0984e3','trait':'#6c5ce7','ai_decision':'#00cec9',
        'agent_created':'#00b894','agent_died':'#636e72',
        'employment':'#fdcb6e','education':'#0984e3',
        'housing':'#e84393','health':'#d63031','medical':'#d63031'
    };
    for(const[k,v]of Object.entries(colors)){if(type.includes(k))return v;}
    return'#a0aec0';
}

// ===== Social Network Modal (ECharts 力导向图) =====
async function showSocialNetworkModal(){
    try{
        let data=null;
        try{
            const r=await fetch('/api/v1/social/network?limit=100',{headers:{'X-API-Key':'yulong-dev-key'}});
            if(r.ok){const d=await r.json();if(d.success)data=d.data;}
        }catch(_){}
        if(!data){
            const r2=await fetch('/api/social/network?limit=100');
            if(r2.ok){const d2=await r2.json();if(d2.success)data=d2.data;}
        }
        if(!data||!data.nodes||!data.nodes.length){alert('暂无社交网络数据');return;}

        // 构建 ECharts graph 数据
        const nodes=(data.nodes||[]).map(function(n){
            return{
                id:String(n.id),name:n.name||('Agent-'+n.id),
                symbolSize:Math.max(8,Math.min(35,(n.value||n.connections||1)*3+5)),
                category:n.group||n.occupation||'其他',
                value:n.value||n.connections||0,
                itemStyle:{color:OCC_CLR[n.group]||OCC_CLR[n.occupation]||'#888'}
            };
        });
        const links=(data.links||data.edges||[]).map(function(l){
            return{
                source:String(l.source),target:String(l.target),
                lineStyle:{
                    color:l.type==='spouse'?'#e84393':(l.type==='friend'?'#00cec9':'#667eea'),
                    width:l.type==='spouse'?2:1,
                    opacity:0.5,
                    curveness:0.1
                }
            };
        });

        // 移除旧模态框
        const old=document.querySelector('.network-modal');
        if(old)old.remove();

        // 弹出模态框
        const modal=document.createElement('div');
        modal.className='network-modal';
        modal.innerHTML=`
            <div class="network-modal-content">
                <div class="network-modal-header">
                    <span>🕸️ 社交关系网络 (${nodes.length}人)</span>
                    <button onclick="this.closest('.network-modal').remove()">✕</button>
                </div>
                <div id="network-modal-chart" style="width:100%;height:500px"></div>
            </div>
        `;
        document.body.appendChild(modal);

        // 点击背景关闭
        modal.addEventListener('click',function(e){if(e.target===modal)modal.remove();});

        const chart=echarts.init(document.getElementById('network-modal-chart'));
        chart.setOption({
            backgroundColor:'transparent',
            tooltip:{
                trigger:'item',
                backgroundColor:'rgba(22,33,62,.95)',
                borderColor:'rgba(102,126,234,.4)',
                textStyle:{color:'#edf2f7',fontSize:11},
                formatter:function(p){return p.dataType==='node'?('<b>'+p.data.name+'</b><br>连接: '+p.data.value):'';}
            },
            series:[{
                type:'graph',layout:'force',roam:true,draggable:true,
                force:{repulsion:100,gravity:0.1,edgeLength:[50,150],layoutAnimation:true},
                data:nodes,links:links,
                label:{show:false},
                lineStyle:{opacity:0.5,curveness:0.1},
                emphasis:{focus:'adjacency',lineStyle:{width:3},label:{show:true,color:'#fff',fontSize:11}},
                animationDuration:1500,animationEasingUpdate:'quinticInOut'
            }]
        });

        // 响应窗口变化
        window.addEventListener('resize',function(){chart.resize();});
    }catch(e){console.warn('showSocialNetworkModal err',e);}
}

// ===== Events =====
function renderEv(){
    const el=document.getElementById('ev-list');
    let evs=S.events;
    if(S.evFlt!=='all')evs=evs.filter(e=>e.type===S.evFlt);
    document.getElementById('ev-cnt').textContent=evs.length+' events';
    if(!evs.length){el.innerHTML='<div class="spinner-w" style="padding:20px"><span style="color:var(--muted)">暂无事件</span></div>';return}
    el.innerHTML=evs.map(e=>`<div class="ev-item${e._new?' new-pulse':''}"><div class="ev-ico">${e.emoji||EV_ICO[e.type]||'📌'}</div><div><div class="ev-txt">${e.text||e.description||''}</div><div class="ev-time">${e.time||e.timestamp||''}</div></div></div>`).join('');
    el.scrollTop=0;
    setTimeout(()=>{S.events.forEach(e=>{e._new=false})},900);
}
function fltEv(t,btn){S.evFlt=t;document.querySelectorAll('.ev-btn').forEach(b=>b.classList.remove('on'));btn.classList.add('on');renderEv()}

function mockEvents(){
    if(!S.agents.length){S.events=[];renderEv();return}
    const types=['birth','death','marriage','job','house'];
    const tpl={birth:a=>`<strong>${a.name}</strong> 来到了这个世界`,death:a=>`<strong>${a.name}</strong> (${a.age}岁) 去世了`,marriage:a=>`<strong>${a.name}</strong> 结婚了 🎊`,job:a=>`<strong>${a.name}</strong> 换了新工作：${a.occupation}`,house:a=>`<strong>${a.name}</strong> 在${a.region||'住宅区'}买了房`};
    const evs=[];for(let i=0;i<Math.min(25,S.agents.length);i++){const a=S.agents[Math.floor(Math.random()*S.agents.length)];const t=types[Math.floor(Math.random()*types.length)];evs.push({type:t,emoji:EV_ICO[t],text:tpl[t](a),time:'Day '+(Math.floor(Math.random()*365)+1)})}
    S.events=evs;renderEv();
}

// ===== ECharts Trend =====
function initTrend(){
    const d=document.getElementById('trend-chart');if(!d)return;
    S.trendChart=echarts.init(d,null,{renderer:'canvas'});
    window.addEventListener('resize',()=>{if(S.trendChart)S.trendChart.resize()});
}

// ===== Trend Metrics =====
const TREND_METRICS={
    population:{name:'人口',color:'#667eea',yAxis:0,area:true},
    avg_income:{name:'收入',color:'#fdcb6e',yAxis:0,area:true},
    employment_rate:{name:'就业率(%)',color:'#00cec9',yAxis:1,area:false},
    satisfaction:{name:'满意度',color:'#e84393',yAxis:1,area:false,dashed:true,transform:v=>v>5?v:+(v*20).toFixed(1)},
    health:{name:'健康',color:'#00b894',yAxis:1,area:false},
    happiness:{name:'幸福',color:'#a29bfe',yAxis:1,area:false,dashed:true},
    crime_rate:{name:'犯罪率',color:'#d63031',yAxis:1,area:false,dashed:true}
};
let _trendRawData=null;
function getActiveTrendKeys(){return [...document.querySelectorAll('#trend-selector input[type=checkbox]')].filter(cb=>cb.checked).map(cb=>cb.dataset.key)}
function onTrendToggle(){
    const active=getActiveTrendKeys();
    if(active.length<1){document.querySelector('#trend-selector input[type=checkbox]').checked=true;return}
    if(active.length>4){[...document.querySelectorAll('#trend-selector input:checked')].pop().checked=false;return}
    if(_trendRawData)renderTrend(_trendRawData);
}
function renderTrend(d){
    if(!S.trendChart)return;
    _trendRawData=d;
    const xData=d.days||d.labels||[];
    const dataMap={population:d.population||(d.series&&d.series.population)||[],avg_income:d.avg_income||(d.series&&d.series.avg_income)||[],employment_rate:d.employment_rate||(d.series&&d.series.employment_rate)||[],satisfaction:d.satisfaction||(d.series&&d.series.avg_satisfaction)||[],health:d.health||(d.series&&d.series.health)||[],happiness:d.happiness||(d.series&&d.series.happiness)||[],crime_rate:d.crime_rate||(d.series&&d.series.crime_rate)||[]};
    const activeKeys=getActiveTrendKeys();const series=[];const legendData=[];
    activeKeys.forEach(key=>{
        const m=TREND_METRICS[key];if(!m)return;let data=dataMap[key]||[];if(m.transform)data=data.map(m.transform);legendData.push(m.name);
        const s={name:m.name,type:'line',data:data,smooth:true,symbol:'none',lineStyle:{width:2,color:m.color},animationDuration:800,animationEasing:'cubicOut'};
        if(m.yAxis===1)s.yAxisIndex=1;if(m.dashed)s.lineStyle.type='dashed';
        if(m.area)s.areaStyle={color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:m.color+'26'},{offset:1,color:'rgba(0,0,0,0)'}])};
        series.push(s);
    });
    S.trendChart.setOption({backgroundColor:'transparent',tooltip:{trigger:'axis',backgroundColor:'rgba(22,33,62,.95)',borderColor:'rgba(102,126,234,.4)',textStyle:{color:'#edf2f7',fontSize:11}},
        legend:{data:legendData,textStyle:{color:'#a0aec0',fontSize:10},top:0,itemWidth:14,itemHeight:3},
        grid:{left:50,right:50,top:30,bottom:22},
        xAxis:{type:'category',data:xData,axisLine:{lineStyle:{color:'rgba(102,126,234,.3)'}},axisLabel:{color:'#718096',fontSize:9},axisTick:{show:false}},
        yAxis:[{type:'value',axisLine:{show:false},axisLabel:{color:'#718096',fontSize:9},splitLine:{lineStyle:{color:'rgba(102,126,234,.08)'}}},{type:'value',axisLine:{show:false},axisLabel:{color:'#718096',fontSize:9},splitLine:{show:false},min:0,max:100}],
        series:series,animation:true,animationDuration:800,animationEasing:'cubicOut'
    },true);
}

function mockTrend(){
    const d=[],p=[],inc=[],e=[],s=[];
    let pp=1000,ii=3000,ee=65,ss=3;
    for(let i=1;i<=24;i++){d.push('M'+i);pp+=Math.floor(Math.random()*20-5);ii+=Math.floor(Math.random()*200-80);ee+=(Math.random()-.45)*2;ss+=(Math.random()-.45)*.1;p.push(Math.max(500,pp));inc.push(Math.max(1000,ii));e.push(+Math.min(100,Math.max(30,ee)).toFixed(1));s.push(+Math.min(5,Math.max(1,ss)).toFixed(2))}
    renderTrend({days:d,population:p,avg_income:inc,employment_rate:e,satisfaction:s});
}

/* ============================================================ */
/* MBTI 分布图 & 能力系统 & 金融可视化 */
/* ============================================================ */

// MBTI 类型颜色映射
const MBTI_COLORS={
    'INTJ':'#b388ff','INTP':'#b388ff','ENTJ':'#b388ff','ENTP':'#b388ff',
    'INFJ':'#69db7c','INFP':'#69db7c','ENFJ':'#69db7c','ENFP':'#69db7c',
    'ISTJ':'#74c0fc','ISFJ':'#74c0fc','ESTJ':'#74c0fc','ESFJ':'#74c0fc',
    'ISTP':'#ffd43b','ISFP':'#ffd43b','ESTP':'#ffd43b','ESFP':'#ffd43b',
    'UNKNOWN':'#718096'
};

const MBTI_GROUPS={
    '分析师 (NT)':['INTJ','INTP','ENTJ','ENTP'],
    '外交官 (NF)':['INFJ','INFP','ENFJ','ENFP'],
    '哨兵 (SJ)':['ISTJ','ISFJ','ESTJ','ESFJ'],
    '探险家 (SP)':['ISTP','ISFP','ESTP','ESFP']
};

let _mbtiDistChart=null;

async function loadMBTIDist(){
    try{
        const r=await fetch('/api/v1/stats/mbti',{headers:{'X-API-Key':'yulong-dev-key'}});
        if(!r.ok)return;
        const d=await r.json();
        if(d.success&&d.data)renderMBTIDist(d.data);
    }catch(e){console.warn('mbti dist err',e)}
}

function renderMBTIDist(data){
    const dom=document.getElementById('mbti-dist-chart');
    if(!dom)return;
    if(!_mbtiDistChart){
        _mbtiDistChart=echarts.init(dom,null,{renderer:'canvas'});
        window.addEventListener('resize',()=>{if(_mbtiDistChart)_mbtiDistChart.resize()});
    }

    const dist=data.distribution||{};
    // 16 种 MBTI 类型有序排列
    const allTypes=['INTJ','INTP','ENTJ','ENTP','INFJ','INFP','ENFJ','ENFP','ISTJ','ISFJ','ESTJ','ESFJ','ISTP','ISFP','ESTP','ESFP'];
    const types=allTypes.filter(t=>dist[t]!==undefined);
    // 如果有 UNKNOWN，追加到末尾
    if(dist['UNKNOWN'])types.push('UNKNOWN');

    const values=types.map(t=>dist[t]||0);
    const colors=types.map(t=>MBTI_COLORS[t]||'#718096');

    _mbtiDistChart.setOption({
        backgroundColor:'transparent',
        tooltip:{
            trigger:'axis',
            backgroundColor:'rgba(22,33,62,.95)',
            borderColor:'rgba(102,126,234,.4)',
            textStyle:{color:'#edf2f7',fontSize:11},
            formatter:function(params){
                const p=params[0];
                return '<b>'+p.name+'</b><br>数量: '+p.value;
            }
        },
        grid:{left:35,right:8,top:8,bottom:45},
        xAxis:{
            type:'category',
            data:types,
            axisLine:{lineStyle:{color:'rgba(102,126,234,.3)'}},
            axisLabel:{color:'#a0aec0',fontSize:8,rotate:45},
            axisTick:{show:false}
        },
        yAxis:{
            type:'value',
            axisLine:{show:false},
            axisLabel:{color:'#718096',fontSize:9},
            splitLine:{lineStyle:{color:'rgba(102,126,234,.08)'}}
        },
        series:[{
            type:'bar',
            data:values.map(function(v,i){return{value:v,itemStyle:{color:colors[i],borderRadius:[3,3,0,0]}}}),
            barWidth:'55%',
            emphasis:{
                itemStyle:{shadowBlur:8,shadowColor:'rgba(0,0,0,.3)'}
            },
            animationDuration:800,
            animationEasing:'cubicOut'
        }]
    },true);
}

// 天赋雷达图渲染
function renderTalentRadar(containerId,talents){
    const dom=document.getElementById(containerId);
    if(!dom||!talents||Object.keys(talents).length===0)return null;

    const chart=echarts.init(dom,null,{renderer:'canvas'});
    const names=Object.keys(talents);
    const values=Object.values(talents);
    const maxVal=Math.max(10,Math.ceil(Math.max(...values)));

    chart.setOption({
        backgroundColor:'transparent',
        tooltip:{
            trigger:'item',
            backgroundColor:'rgba(22,33,62,.95)',
            borderColor:'rgba(102,126,234,.4)',
            textStyle:{color:'#edf2f7',fontSize:11}
        },
        radar:{
            indicator:names.map(function(n){return{name:n,max:maxVal}}),
            shape:'polygon',
            splitNumber:4,
            axisName:{color:'#a0aec0',fontSize:9},
            splitLine:{lineStyle:{color:'rgba(102,126,234,.15)'}},
            splitArea:{areaStyle:{color:['rgba(102,126,234,.02)','rgba(102,126,234,.05)']}},
            axisLine:{lineStyle:{color:'rgba(102,126,234,.2)'}},
            center:['50%','55%'],
            radius:'70%'
        },
        series:[{
            type:'radar',
            data:[{
                value:values,
                name:'天赋',
                areaStyle:{color:'rgba(102,126,234,.2)'},
                lineStyle:{color:'#667eea',width:2},
                itemStyle:{color:'#667eea'},
                symbol:'circle',
                symbolSize:5
            }],
            animationDuration:600
        }]
    },true);
    return chart;
}

// 技能等级 → tier 名称
function getSkillTierClass(tier){
    if(!tier)return'tier-common';
    const t=tier.toLowerCase();
    if(t==='legendary')return'tier-legendary';
    if(t==='epic')return'tier-epic';
    if(t==='rare')return'tier-rare';
    if(t==='uncommon')return'tier-uncommon';
    return'tier-common';
}

function getSkillTierLabel(tier){
    const map={'common':'普通','uncommon':'优秀','rare':'稀有','epic':'史诗','legendary':'传说'};
    return map[(tier||'').toLowerCase()]||tier||'普通';
}

// 特质标签颜色
function getTraitTagClass(index){
    const classes=['trait-gold','trait-purple','trait-cyan'];
    return classes[index%classes.length];
}

// 格式化金额
function formatMoney(v){
    if(v===undefined||v===null)return'--';
    if(v>=10000)return'$'+(v/10000).toFixed(1)+'万';
    return'$'+Math.round(v).toLocaleString();
}

// ===== Agent Chat (上帝视角) =====
async function sendChat(agentId){
    const input=document.getElementById('chat-input');
    if(!input)return;
    const msg=input.value.trim();
    if(!msg)return;
    input.value='';
    input.focus();
    
    const msgDiv=document.getElementById('chat-messages');
    if(!msgDiv)return;
    
    // 显示用户消息
    msgDiv.innerHTML+=`<div class="chat-msg chat-msg-user"><span class="chat-msg-label">你</span>${escapeHtml(msg)}</div>`;
    msgDiv.scrollTop=msgDiv.scrollHeight;
    
    // 显示加载中
    const loadingId='chat-loading-'+Date.now();
    msgDiv.innerHTML+=`<div class="chat-msg chat-msg-agent" id="${loadingId}"><span class="chat-msg-label">💬</span><span class="chat-typing">思考中...</span></div>`;
    msgDiv.scrollTop=msgDiv.scrollHeight;
    
    try{
        const res=await fetch('/api/v1/agents/'+agentId+'/chat',{
            method:'POST',
            headers:{'Content-Type':'application/json','X-API-Key':'yulong-dev-key'},
            body:JSON.stringify({message:msg})
        });
        const data=await res.json();
        const reply=data.data?.response||'...';
        const eng=data.data?.engine_used||'';
        
        // 替换加载消息
        const loadingEl=document.getElementById(loadingId);
        if(loadingEl){
            const engBadge=eng&&eng!=='template'?`<span class="chat-engine-badge">${eng}</span>`:'';
            loadingEl.innerHTML=`<span class="chat-msg-label">💬</span>${escapeHtml(reply)}${engBadge}`;
        }
    }catch(e){
        const loadingEl=document.getElementById(loadingId);
        if(loadingEl){
            loadingEl.innerHTML=`<span class="chat-msg-label">💬</span><span style="color:var(--muted)">（无法回复）</span>`;
        }
    }
    msgDiv.scrollTop=msgDiv.scrollHeight;
}

function escapeHtml(text){
    const div=document.createElement('div');
    div.textContent=text;
    return div.innerHTML;
}

/* ============================================================ */
/* 组件1: 实验模板选择页面 JS */
/* ============================================================ */

const EXPERIMENT_TEMPLATES = [
  { id: 'edu_001', name: '教育政策验证', cat: 'education', icon: '📚',
    desc: '测试不同教育政策对学生升学率和就业的影响',
    months: 216, agents: 5000,
    metrics: ['升学率', '就业率', '平均收入', '教育满意度'],
    params: { education_policy: 'baseline', university_capacity: 0.5 } },
  { id: 'edu_002', name: '教育公平性研究', cat: 'education', icon: '📚',
    desc: '研究不同社会经济背景学生的教育机会差异',
    months: 144, agents: 10000,
    metrics: ['阶层流动性', '教育基尼系数', '奖学金覆盖率'],
    params: { income_inequality: 0.4, scholarship_coverage: 0.3 } },
  { id: 'edu_003', name: '在线教育影响', cat: 'education', icon: '📚',
    desc: '评估在线教育对传统教育的冲击和补充作用',
    months: 60, agents: 3000,
    metrics: ['在线课程注册率', '学习效果对比', '成本效益'],
    params: { online_platform_adoption: 0.5, internet_access: 0.9 } },
  { id: 'edu_004', name: '终身学习社会', cat: 'education', icon: '📚',
    desc: '模拟终身学习文化对职业发展的影响',
    months: 240, agents: 5000,
    metrics: ['成人学习参与率', '职业转换率', '收入增长'],
    params: { lifelong_learning_culture: 0.7, employer_training_support: 0.5 } },

  { id: 'biz_001', name: '产品上市策略', cat: 'business', icon: '💼',
    desc: '测试不同产品上市策略的市场表现',
    months: 36, agents: 10000,
    metrics: ['市场渗透率', '用户增长率', '客户满意度', '利润率'],
    params: { launch_strategy: 'premium', marketing_budget: 1000000 } },
  { id: 'biz_002', name: '营销策略对比', cat: 'business', icon: '💼',
    desc: '对比不同营销策略的 ROI',
    months: 24, agents: 5000,
    metrics: ['转化率', '客户获取成本', '品牌知名度', 'ROI'],
    params: { strategy_a: 'digital_marketing', budget_split: 0.5 } },
  { id: 'biz_003', name: '组织变革管理', cat: 'business', icon: '💼',
    desc: '模拟企业组织变革对员工满意度和绩效的影响',
    months: 18, agents: 2000,
    metrics: ['员工满意度', '离职率', '生产率', '变革接受度'],
    params: { change_type: 'digital_transformation', communication_quality: 0.7 } },
  { id: 'biz_004', name: '创业生态系统', cat: 'business', icon: '💼',
    desc: '研究创业生态系统对创新和就业的影响',
    months: 60, agents: 10000,
    metrics: ['创业率', '初创企业存活率', '创新指数', '就业创造'],
    params: { vc_availability: 0.5, failure_tolerance: 0.7 } },

  { id: 'pol_001', name: '税收政策评估', cat: 'policy', icon: '🏛️',
    desc: '评估不同税收政策对经济和社会的影响',
    months: 60, agents: 10000,
    metrics: ['GDP 增长', '贫富差距', '税收收入', '投资率'],
    params: { tax_system: 'progressive', corporate_tax_rate: 0.25 } },
  { id: 'pol_002', name: '全民基本收入', cat: 'policy', icon: '🏛️',
    desc: '模拟 UBI 对就业、贫困和幸福感的影响',
    months: 60, agents: 10000,
    metrics: ['就业率', '贫困率', '幸福感', '创业率'],
    params: { ubi_amount: 2000, funding_source: 'income_tax' } },
  { id: 'pol_003', name: '住房政策研究', cat: 'policy', icon: '🏛️',
    desc: '研究住房政策对房价和自有率的影响',
    months: 120, agents: 5000,
    metrics: ['房价收入比', '住房自有率', '租房负担', '无家可归率'],
    params: { policy_type: 'affordable_housing', public_housing_ratio: 0.2 } },
  { id: 'pol_004', name: '医疗改革方案', cat: 'policy', icon: '🏛️',
    desc: '比较不同医疗体系的成本和效果',
    months: 120, agents: 10000,
    metrics: ['人均医疗支出', '预期寿命', '满意度', '等待时间'],
    params: { system_type: 'single_payer', government_funding: 0.7 } },

  { id: 'soc_001', name: '城市化进程', cat: 'social', icon: '👥',
    desc: '模拟城市化对经济、环境和社会的影响',
    months: 240, agents: 20000,
    metrics: ['城市化率', '城乡收入差距', '通勤时间', '生活质量'],
    params: { urban_job_growth: 0.03, migration_policy: 'open' } },
  { id: 'soc_002', name: '人口老龄化', cat: 'social', icon: '👥',
    desc: '研究老龄化社会对经济和福利系统的挑战',
    months: 360, agents: 10000,
    metrics: ['抚养比', '养老金可持续性', '医疗支出', '劳动力供给'],
    params: { fertility_rate: 1.5, retirement_age: 65 } },
  { id: 'soc_003', name: '社会流动性', cat: 'social', icon: '👥',
    desc: '研究影响社会阶层流动性的因素',
    months: 240, agents: 10000,
    metrics: ['代际收入弹性', '教育流动性', '职业流动性'],
    params: { meritocracy_level: 0.7, discrimination_level: 0.1 } },
  { id: 'soc_004', name: '文化融合', cat: 'social', icon: '👥',
    desc: '模拟多元文化社会的融合过程',
    months: 240, agents: 10000,
    metrics: ['文化多样性指数', '社会凝聚力', '歧视事件', '通婚率'],
    params: { immigration_rate: 0.02, integration_policy: 'multicultural' } },

  { id: 'hlt_001', name: '流行病传播', cat: 'health', icon: '🏥',
    desc: '模拟传染病传播和防控措施效果',
    months: 24, agents: 10000,
    metrics: ['感染率', '死亡率', '医疗挤兑', '经济损失'],
    params: { r0: 2.5, fatality_rate: 0.02, intervention: 'lockdown' } },
  { id: 'hlt_002', name: '心理健康危机', cat: 'health', icon: '🏥',
    desc: '研究社会压力对心理健康的影响',
    months: 60, agents: 5000,
    metrics: ['抑郁率', '焦虑率', '自杀率', '治疗覆盖率'],
    params: { social_pressure: 0.7, mental_health_services: 0.6 } },
  { id: 'hlt_003', name: '健康生活方式推广', cat: 'health', icon: '🏥',
    desc: '评估健康生活方式干预的效果',
    months: 60, agents: 5000,
    metrics: ['肥胖率', '运动参与率', '慢性病发病率', '医疗支出'],
    params: { intervention_type: 'education', healthy_food_access: 0.7 } },
  { id: 'hlt_004', name: '医疗资源分配', cat: 'health', icon: '🏥',
    desc: '优化医疗资源分配策略',
    months: 120, agents: 10000,
    metrics: ['等待时间', '治疗可及性', '健康结果', '成本效益'],
    params: { allocation_method: 'need_based', telemedicine_adoption: 0.6 } },

  { id: 'tech_001', name: '技术扩散模式', cat: 'tech', icon: '💻',
    desc: '研究新技术在社会中的扩散规律',
    months: 120, agents: 10000,
    metrics: ['采用率', '扩散速度', '创新者比例', '数字鸿沟'],
    params: { innovation_type: 'disruptive', network_effect: 0.7 } },
  { id: 'tech_002', name: 'AI 自动化影响', cat: 'tech', icon: '💻',
    desc: '评估 AI 自动化对就业和经济的影响',
    months: 120, agents: 10000,
    metrics: ['失业率', '生产率', '收入不平等', '新岗位创造'],
    params: { automation_rate: 0.03, reskilling_program: 0.5 } },
  { id: 'tech_003', name: '社交媒体影响', cat: 'tech', icon: '💻',
    desc: '研究社交媒体对信息传播和社会舆论的影响',
    months: 36, agents: 10000,
    metrics: ['信息传播速度', '极化程度', '假新闻传播', '社会信任'],
    params: { platform_penetration: 0.7, fact_checking: 0.6 } },
  { id: 'tech_004', name: '绿色技术转型', cat: 'tech', icon: '💻',
    desc: '模拟绿色技术转型的经济和环境效应',
    months: 240, agents: 10000,
    metrics: ['碳排放', '绿色就业', '转型成本', '能源独立性'],
    params: { carbon_tax: 50, renewable_subsidy: 0.3 } },
];

const CAT_NAMES = {
  education: '📚 教育', business: '💼 商业', policy: '🏛️ 政策',
  social: '👥 社会', health: '🏥 健康', tech: '💻 科技'
};

let selectedTemplate = null;
let currentCatFilter = 'all';

function initExperimentPicker() {
  renderTemplateCards();
}

function renderTemplateCards(category) {
  category = category || 'all';
  const grid = document.getElementById('expGrid');
  const templates = category === 'all'
    ? EXPERIMENT_TEMPLATES
    : EXPERIMENT_TEMPLATES.filter(function(t){ return t.cat === category; });

  grid.innerHTML = templates.map(function(t){
    return '<div class="exp-card" data-cat="'+t.cat+'" data-id="'+t.id+'" onclick="selectTemplate(\''+t.id+'\')">'
      + '<div class="exp-card-id"><span class="exp-cat-icon">'+t.icon+'</span> '+t.id+'</div>'
      + '<div class="exp-card-name">'+t.name+'</div>'
      + '<div class="exp-card-desc">'+t.desc+'</div>'
      + '<div class="exp-card-meta">'
      + '<span class="exp-card-tag">👥 '+t.agents.toLocaleString()+'</span>'
      + '<span class="exp-card-tag">📅 '+t.months+'月</span>'
      + '<span class="exp-card-tag">📊 '+t.metrics.length+'指标</span>'
      + '</div>'
      + '<div class="exp-card-metrics">'
      + t.metrics.map(function(m){ return '<span class="exp-metric-chip">'+m+'</span>'; }).join('')
      + '</div></div>';
  }).join('');
}

function filterCategory(cat, btn) {
  currentCatFilter = cat;
  document.querySelectorAll('.exp-cat-btn').forEach(function(b){ b.classList.remove('active'); });
  btn.classList.add('active');
  renderTemplateCards(cat);

  if (selectedTemplate && cat !== 'all') {
    var t = EXPERIMENT_TEMPLATES.find(function(t){ return t.id === selectedTemplate; });
    if (t && t.cat !== cat) {
      selectedTemplate = null;
      document.getElementById('expConfigPanel').style.display = 'none';
    }
  }
  if (selectedTemplate) {
    var card = document.querySelector('.exp-card[data-id="'+selectedTemplate+'"]');
    if (card) card.classList.add('selected');
  }
}

function selectTemplate(templateId) {
  var t = EXPERIMENT_TEMPLATES.find(function(t){ return t.id === templateId; });
  if (!t) return;

  selectedTemplate = templateId;
  document.querySelectorAll('.exp-card').forEach(function(c){ c.classList.remove('selected'); });
  var card = document.querySelector('.exp-card[data-id="'+templateId+'"]');
  if (card) card.classList.add('selected');

  document.getElementById('expConfigPanel').style.display = '';
  document.getElementById('expConfigName').textContent = '['+t.id+'] '+t.name;
  document.getElementById('cfgAgentCount').value = t.agents;
  document.getElementById('cfgMonths').value = t.months;
  document.getElementById('cfgWorldName').value = 'world_'+t.id.replace('_', '');

  var extra = document.getElementById('expConfigExtra');
  var paramEntries = Object.entries(t.params);
  if (paramEntries.length > 0) {
    extra.innerHTML = '<div style="font-size:0.82em;color:var(--muted);margin-bottom:10px;font-weight:600">📋 模板专属参数</div>'
      + '<div class="exp-config-row">'
      + paramEntries.map(function(kv){
          return '<div class="exp-config-field"><label>'+kv[0]+'</label>'
            + '<input type="text" value="'+kv[1]+'" data-param="'+kv[0]+'" class="exp-extra-param">'
            + '</div>';
        }).join('')
      + '</div>';
  } else {
    extra.innerHTML = '';
  }

  document.getElementById('expConfigPanel').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function cancelExperiment() {
  selectedTemplate = null;
  document.querySelectorAll('.exp-card').forEach(function(c){ c.classList.remove('selected'); });
  document.getElementById('expConfigPanel').style.display = 'none';
  document.getElementById('expPickerOverlay').classList.add('hidden');
}

async function launchExperiment() {
  if (!selectedTemplate) return;

  var t = EXPERIMENT_TEMPLATES.find(function(t){ return t.id === selectedTemplate; });
  var btn = document.getElementById('expLaunchBtn');
  btn.classList.add('loading');
  btn.textContent = '⏳ 启动中...';

  var config = {
    template_id: selectedTemplate,
    agent_count: parseInt(document.getElementById('cfgAgentCount').value),
    duration_months: parseInt(document.getElementById('cfgMonths').value),
    speed: parseInt(document.getElementById('cfgSpeed').value),
    world_name: document.getElementById('cfgWorldName').value,
    extra_params: {},
  };

  document.querySelectorAll('.exp-extra-param').forEach(function(el){
    config.extra_params[el.dataset.param] = el.value;
  });

  try {
    var resp = await fetch('/api/experiment/launch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    var data = await resp.json();

    if (data.error) {
      alert('启动失败: ' + data.error);
      btn.classList.remove('loading');
      btn.textContent = '🚀 启动实验';
      return;
    }

    document.getElementById('expPickerOverlay').classList.add('hidden');

    S.world = config.world_name;
    simState.running = true;
    simState.speed = config.speed;
    simState.currentMonth = 0;
    simState.totalMonths = config.duration_months;
    simState.templateId = selectedTemplate;
    simState.templateName = t.name;

    updateSimControlUI();
    loadAll();
  } catch (e) {
    alert('启动失败: ' + e.message);
  } finally {
    btn.classList.remove('loading');
    btn.textContent = '🚀 启动实验';
  }
}

function showExperimentPicker() {
  document.getElementById('expPickerOverlay').classList.remove('hidden');
}

/* ============================================================ */
/* 组件2: 模拟控制面板 JS */
/* ============================================================ */

var simState = {
  running: false,
  paused: false,
  speed: 10,
  currentMonth: 0,
  totalMonths: 0,
  templateId: null,
  templateName: '',
  intervalId: null,
};

function simTogglePlay() {
  if (!simState.running) {
    showExperimentPicker();
    return;
  }

  simState.paused = !simState.paused;
  updateSimControlUI();

  if (simState.paused) {
    if (simState.intervalId) {
      clearInterval(simState.intervalId);
      simState.intervalId = null;
    }
  } else {
    startSimLoop();
  }
}

function simSetSpeed(speed, btn) {
  simState.speed = speed;
  document.querySelectorAll('.sim-speed-btn').forEach(function(b){ b.classList.remove('active'); });
  if (btn) btn.classList.add('active');

  if (simState.running && !simState.paused) {
    if (simState.intervalId) clearInterval(simState.intervalId);
    startSimLoop();
  }
}

function simStop() {
  if (!simState.running) return;
  if (!confirm('确定要停止当前实验吗？')) return;

  simState.running = false;
  simState.paused = false;
  simState.currentMonth = 0;
  if (simState.intervalId) {
    clearInterval(simState.intervalId);
    simState.intervalId = null;
  }
  updateSimControlUI();
}

function startSimLoop() {
  if (simState.intervalId) clearInterval(simState.intervalId);

  var intervalMs, monthsPerTick;
  if (simState.speed <= 10) {
    intervalMs = Math.max(200, 1000 / simState.speed);
    monthsPerTick = 1;
  } else {
    intervalMs = 200;
    monthsPerTick = Math.ceil(simState.speed / 5);
  }

  simState.intervalId = setInterval(async function(){
    if (simState.paused || !simState.running) return;

    try {
      var resp = await fetch('/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          world: S.world,
          months: monthsPerTick,
          template_id: simState.templateId,
        }),
      });
      var data = await resp.json();

      if (data.current_month !== undefined) {
        simState.currentMonth = data.current_month;
      } else {
        simState.currentMonth += monthsPerTick;
      }

      if (simState.totalMonths > 0 && simState.currentMonth >= simState.totalMonths) {
        simState.currentMonth = simState.totalMonths;
        simState.running = false;
        simState.paused = false;
        clearInterval(simState.intervalId);
        simState.intervalId = null;
        showReportPanel();
      }

      updateSimControlUI();
      loadStats();
      loadAgents();
    } catch (e) {
      console.warn('simulate tick error:', e);
    }
  }, intervalMs);
}

function updateSimControlUI() {
  var playBtn = document.getElementById('simPlayBtn');
  var playIcon = document.getElementById('simPlayIcon');
  var progressBar = document.getElementById('simProgressBar');
  var progressText = document.getElementById('simProgressText');
  var expName = document.getElementById('simExpName');

  if (simState.running && !simState.paused) {
    playIcon.textContent = '⏸';
    playBtn.classList.add('playing');
  } else {
    playIcon.textContent = '▶️';
    playBtn.classList.remove('playing');
  }

  var pct = simState.totalMonths > 0
    ? (simState.currentMonth / simState.totalMonths * 100).toFixed(1)
    : 0;
  progressBar.style.width = pct + '%';
  progressText.textContent = '第 ' + simState.currentMonth + ' / ' + simState.totalMonths + ' 月';

  expName.textContent = simState.templateName || '--';
}

/* ---- 快速模拟（无需实验模板，直接推进 N 月） ---- */
async function quickSimulate(months) {
    var statusEl = document.getElementById('simProgressText');
    if (statusEl) statusEl.textContent = '模拟中...';
    try {
        var res = await fetch('/api/v1/simulate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({months: months})
        });
        var data = await res.json();
        var mo = data.data?.months_simulated || data.months_simulated || '?';
        if (statusEl) statusEl.textContent = '已模拟: ' + mo + '月';
        loadAll();
    } catch(e) {
        if (statusEl) statusEl.textContent = '模拟失败';
        console.warn('quickSimulate error:', e);
    }
}

/* ============================================================ */
/* 组件3: 报告生成面板 JS */
/* ============================================================ */

function toggleReportPanel() {
  var panel = document.getElementById('reportPanel');
  var fab = document.getElementById('reportFab');
  var isVisible = panel.style.display !== 'none';

  if (isVisible) {
    panel.style.display = 'none';
    fab.classList.remove('active');
  } else {
    panel.style.display = '';
    fab.classList.add('active');
    updateReportInfo();
  }
}

function showReportPanel() {
  document.getElementById('reportPanel').style.display = '';
  document.getElementById('reportFab').classList.add('active');
  updateReportInfo();
}

function updateReportInfo() {
  document.getElementById('rptExpName').textContent =
    simState.templateName || '自由探索';
  document.getElementById('rptProgress').textContent =
    simState.currentMonth + ' / ' + (simState.totalMonths || '∞') + ' 月';
  document.getElementById('rptWorld').textContent = S.world;
}

async function generateReport() {
  var btn = document.getElementById('rptGenerateBtn');
  var progressWrap = document.getElementById('rptProgressBar');
  var progressInner = document.getElementById('rptProgressInner');

  var formatEl = document.querySelector('input[name="rptFormat"]:checked');
  var format = formatEl ? formatEl.value : 'excel';

  var contents = [];
  document.querySelectorAll('.report-check input:checked').forEach(function(cb){
    contents.push(cb.dataset.content);
  });

  if (contents.length === 0) {
    alert('请至少选择一项报告内容');
    return;
  }

  btn.classList.add('loading');
  btn.textContent = '⏳ 生成中...';
  progressWrap.style.display = '';
  progressInner.style.width = '10%';

  try {
    var progress = 10;
    var progressTimer = setInterval(function(){
      progress = Math.min(progress + Math.random() * 15, 90);
      progressInner.style.width = progress + '%';
    }, 300);

    var resp = await fetch('/api/report/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        world: S.world,
        format: format,
        contents: contents,
        template_id: simState.templateId,
        current_month: simState.currentMonth,
      }),
    });

    clearInterval(progressTimer);
    progressInner.style.width = '100%';

    if (!resp.ok) {
      throw new Error('生成失败: ' + resp.status);
    }

    var blob = await resp.blob();
    var ext = { excel: 'xlsx', csv: 'csv', markdown: 'md', json: 'json' }[format] || 'xlsx';
    var filename = 'report_' + S.world + '_' + new Date().toISOString().slice(0,10) + '.' + ext;

    var url = window.URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);

    btn.textContent = '✅ 已下载';
    setTimeout(function(){
      btn.textContent = '📥 生成并下载';
      btn.classList.remove('loading');
      progressWrap.style.display = 'none';
      progressInner.style.width = '0%';
    }, 2000);

  } catch (e) {
    console.error('Report generation error:', e);

    try {
      await generateLocalReport(format, contents);
      btn.textContent = '✅ 已下载（本地生成）';
    } catch (localErr) {
      alert('报告生成失败: ' + e.message);
      btn.textContent = '📥 生成并下载';
    }

    setTimeout(function(){
      btn.textContent = '📥 生成并下载';
      btn.classList.remove('loading');
      progressWrap.style.display = 'none';
      progressInner.style.width = '0%';
    }, 2000);
  }
}

async function generateLocalReport(format, contents) {
  var statsResp = await fetch('/api/stats?world=' + S.world);
  var statsRaw = await statsResp.json();
  var statsData = statsRaw.data || statsRaw;
  var agentsResp = await fetch('/api/agents?world=' + S.world);
  var agentsRaw = await agentsResp.json();
  var agentsData = agentsRaw.data || agentsRaw;
  var trendsResp = await fetch('/api/trends?world=' + S.world);
  var trendsData = await trendsResp.json();

  var reportContent = '';
  var timestamp = new Date().toISOString().replace('T', ' ').slice(0, 19);

  if (format === 'markdown') {
    reportContent = generateMarkdownReport(statsData, agentsData, trendsData, contents, timestamp);
  } else if (format === 'csv') {
    reportContent = generateCSVReport(statsData, agentsData, trendsData, contents);
  } else if (format === 'json') {
    reportContent = JSON.stringify({
      meta: { world: S.world, template: simState.templateId, generated: timestamp, month: simState.currentMonth },
      stats: contents.includes('summary') ? statsData : undefined,
      agents: contents.includes('agents') ? agentsData.agents : undefined,
      trends: contents.includes('kpi') ? trendsData : undefined,
      events: contents.includes('events') ? S.events : undefined,
    }, null, 2);
  } else {
    reportContent = generateCSVReport(statsData, agentsData, trendsData, contents);
    format = 'csv';
  }

  var ext = { markdown: 'md', csv: 'csv', json: 'json', excel: 'csv' }[format] || 'txt';
  var blob = new Blob([reportContent], { type: 'text/plain;charset=utf-8' });
  var filename = 'report_' + S.world + '_' + new Date().toISOString().slice(0,10) + '.' + ext;
  var url = window.URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
  window.URL.revokeObjectURL(url);
}

function generateMarkdownReport(stats, agents, trends, contents, timestamp) {
  var md = '# 🧪 实验报告\\n\\n';
  md += '> 生成时间：' + timestamp + '\\n';
  md += '> 世界：' + S.world + '\\n';
  md += '> 模板：' + (simState.templateId || '自由探索') + ' - ' + (simState.templateName || '--') + '\\n';
  md += '> 进度：第 ' + simState.currentMonth + ' / ' + (simState.totalMonths || '∞') + ' 月\\n\\n';

  if (contents.includes('summary')) {
    md += '## 📊 实验摘要\\n\\n';
    md += '| 指标 | 数值 |\\n|------|------|\\n';
    md += '| 总人口 | ' + ((stats.population || 0).toLocaleString()) + ' |\\n';
    md += '| 就业率 | ' + (stats.employment_rate || '--') + '% |\\n';
    md += '| 平均月收入 | $' + Math.round(stats.avg_income || 0).toLocaleString() + ' |\\n';
    md += '| 平均满意度 | ' + (stats.avg_satisfaction || '--') + ' |\\n\\n';

    if (stats.occupation) {
      md += '### 职业分布\\n\\n';
      md += '| 职业 | 人数 |\\n|------|------|\\n';
      for (var occ in stats.occupation) {
        md += '| ' + occ + ' | ' + stats.occupation[occ] + ' |\\n';
      }
      md += '\\n';
    }
  }

  if (contents.includes('kpi') && trends.days) {
    md += '## 📈 KPI 趋势\\n\\n';
    md += '| 时间 | 人口 | 收入 | 就业率(%) | 满意度 |\\n';
    md += '|------|------|------|-----------|--------|\\n';
    for (var i = 0; i < trends.days.length; i++) {
      md += '| ' + trends.days[i] + ' | ' + (trends.population?trends.population[i]:'--') + ' | ' + (trends.avg_income?trends.avg_income[i]:'--') + ' | ' + (trends.employment_rate?trends.employment_rate[i]:'--') + ' | ' + (trends.satisfaction?trends.satisfaction[i]:'--') + ' |\\n';
    }
    md += '\\n';
  }

  if (contents.includes('agents') && agents.agents) {
    md += '## 👥 Agent 样本数据 (前 20)\\n\\n';
    md += '| ID | 姓名 | 年龄 | 职业 | 月收入 | 满意度 | 区域 |\\n';
    md += '|----|------|------|------|--------|--------|------|\\n';
    agents.agents.slice(0, 20).forEach(function(a){
      md += '| ' + a.id + ' | ' + a.name + ' | ' + a.age + ' | ' + a.occupation + ' | $' + (a.income||0).toLocaleString() + ' | ' + a.satisfaction + ' | ' + a.region + ' |\\n';
    });
    md += '\\n... 共 ' + agents.total + ' 个 Agent\\n\\n';
  }

  if (contents.includes('events') && S.events.length > 0) {
    md += '## 📰 最近事件\\n\\n';
    S.events.slice(0, 30).forEach(function(ev){
      md += '- ' + (ev.emoji || '📌') + ' **' + (ev.time || '') + '** ' + (ev.text || '') + '\\n';
    });
    md += '\\n';
  }

  md += '---\\n\\n_报告由御龙军虚拟 Agent 世界系统自动生成_\\n';
  return md;
}

function generateCSVReport(stats, agents, trends, contents) {
  var csv = '';

  if (contents.includes('agents') && agents.agents) {
    csv += 'ID,Name,Age,Gender,Occupation,Region,Income,Skill,Education,Satisfaction\\n';
    agents.agents.forEach(function(a){
      csv += a.id + ',"' + a.name + '",' + a.age + ',' + a.gender + ',' + a.occupation + ',' + a.region + ',' + (a.income||0) + ',' + (a.skill_level||0) + ',"' + (a.education||'') + '",' + (a.satisfaction||0) + '\\n';
    });
  } else if (contents.includes('kpi') && trends.days) {
    csv += 'Time,Population,AvgIncome,EmploymentRate,Satisfaction\\n';
    for (var i = 0; i < trends.days.length; i++) {
      csv += (trends.days[i]||'') + ',' + (trends.population?trends.population[i]:'') + ',' + (trends.avg_income?trends.avg_income[i]:'') + ',' + (trends.employment_rate?trends.employment_rate[i]:'') + ',' + (trends.satisfaction?trends.satisfaction[i]:'') + '\\n';
    }
  }

  return csv;
}

// 修改 DOMContentLoaded 初始化
(function(){
  var origInit = null;
  document.addEventListener('DOMContentLoaded', function(){
    initExperimentPicker();
  });
})();
// ── Tab 切换 (Phase 3 Fix6) ──
function switchDetailTab(tab, btn) {
    document.querySelectorAll('.dtab-content').forEach(d => d.style.display = 'none');
    document.querySelectorAll('.dtab').forEach(b => b.classList.remove('active'));
    var el = document.getElementById('dtab-' + tab);
    if (el) el.style.display = 'block';
    if (btn) btn.classList.add('active');
}

async function loadAgentStory(agentId) {
    var panel = document.getElementById('agent-story-panel');
    if (!panel) return;
    try {
        var r = await fetch('/api/agents/' + agentId + '/story');
        if (!r.ok) return;
        var d = await r.json();
        if (d.success && d.data && d.data.story) {
            panel.innerHTML = '<div style="margin-top:10px;padding:10px;background:rgba(102,126,234,.08);border-radius:8px;font-size:.82em;color:var(--text2);line-height:1.5">' + d.data.story.replace(/\n/g,'<br>') + '</div>';
        }
    } catch(_) {}
}

// ===== Phase3 Fix11: 手风琴折叠 =====
function toggleAccordion(header) {
    var body = header.nextElementSibling;
    var arrow = header.querySelector('.acc-arrow');
    if (body.style.display === 'none') {
        body.style.display = 'block';
        arrow.textContent = '▼';
        // 触发 ECharts resize（图表可能在隐藏时未渲染）
        setTimeout(function() {
            var charts = body.querySelectorAll('[id$="-chart"], [id$="-wrap"] > div');
            charts.forEach(function(el) {
                var inst = echarts.getInstanceByDom(el);
                if (inst) inst.resize();
            });
        }, 100);
    } else {
        body.style.display = 'none';
        arrow.textContent = '▶';
    }
}
