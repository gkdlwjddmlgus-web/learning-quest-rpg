import streamlit as st


def inject_styles() -> None:
    st.markdown("""
<style>
.block-container{max-width:1200px;padding-top:1.2rem}
.quest-card{padding:1.2rem 1.4rem;border:1px solid rgba(120,120,140,.25);border-radius:16px;background:rgba(120,120,160,.06);margin:.8rem 0 1rem}
.question-box{padding:1.1rem 1.2rem;border-left:5px solid #6c7ae0;border-radius:8px;background:rgba(110,120,190,.07);font-size:1.08rem;font-weight:600;line-height:1.8}
.game-card{padding:1rem;border:1px solid rgba(120,120,140,.2);border-radius:12px;background:rgba(100,110,160,.05);margin:.4rem 0}
.boss{border:2px solid rgba(180,80,80,.5)}

/* Streamlit default multipage navigation: hide it so PLAYER STATUS starts at the top. */
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavItems"] {
    display:none!important;
}

/*
Streamlit 버전에 따라 sidebar 내부가 nav 요소로 감싸질 수 있으므로
section[data-testid="stSidebar"] nav 전체를 숨기면 실제 사이드바 HUD까지
사라질 수 있다. 기본 multipage navigation testid만 선택적으로 숨긴다.
*/
[data-testid="stSidebar"] > div:first-child {
    padding-top:0!important;
}

/* Sidebar HUD */
[data-testid="stSidebar"]{border-right:1px solid rgba(120,120,140,.16)}
[data-testid="stSidebar"] .block-container{padding-top:1.05rem;padding-left:1rem;padding-right:1rem}
.hud-card{padding:1rem;border:1px solid rgba(110,120,160,.22);border-radius:18px;background:linear-gradient(145deg,rgba(104,117,214,.10),rgba(120,120,160,.035));box-shadow:0 8px 24px rgba(20,25,50,.045);margin:.25rem 0 .75rem}
.hud-eyebrow{font-size:.70rem;letter-spacing:.10em;font-weight:800;opacity:.58;margin-bottom:.25rem}
.hud-title{font-size:1.05rem;font-weight:800;line-height:1.25;margin-bottom:.14rem}
.hud-subtitle{font-size:.75rem;opacity:.67;margin-bottom:.8rem}
.hud-level-row{display:flex;justify-content:space-between;align-items:end;margin:.15rem 0 .3rem}
.hud-level{font-size:1.75rem;font-weight:900;line-height:1}
.hud-xp{font-size:.72rem;opacity:.68}
.hud-bar{height:8px;border-radius:999px;background:rgba(120,120,140,.14);overflow:hidden;margin-bottom:.9rem}
.hud-bar-fill{height:100%;border-radius:999px;background:linear-gradient(90deg,#ff4b4b,#ff8a5b)}
.hud-hp-row{display:flex;justify-content:space-between;align-items:center;font-size:.78rem;margin-bottom:.35rem}
.hud-hp-value{font-weight:800}
.hud-hp-bar{height:7px;border-radius:999px;background:rgba(120,120,140,.14);overflow:hidden;margin-bottom:.85rem}
.hud-hp-fill{height:100%;border-radius:999px;background:linear-gradient(90deg,#ef476f,#ff6b81)}
.hud-grid{display:grid;grid-template-columns:1fr 1fr;gap:.42rem}
.hud-stat{padding:.55rem .6rem;border:1px solid rgba(120,120,140,.15);border-radius:12px;background:rgba(255,255,255,.34)}
.hud-stat-label{font-size:.66rem;opacity:.62;margin-bottom:.08rem}
.hud-stat-value{font-size:.88rem;font-weight:800}
.hud-resource-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:.38rem;margin-top:.48rem}
.hud-resource{text-align:center;padding:.5rem .2rem;border-radius:11px;background:rgba(110,120,160,.06);border:1px solid rgba(120,120,140,.12)}
.hud-resource-value{font-size:.9rem;font-weight:850}
.hud-resource-label{font-size:.60rem;opacity:.58;margin-top:.08rem}
.hud-section-title{font-size:.72rem;letter-spacing:.08em;font-weight:850;opacity:.63;margin:.9rem 0 .38rem}
.hud-world{padding:.78rem .85rem;border:1px solid rgba(70,160,130,.19);border-radius:14px;background:rgba(55,180,130,.055);margin-bottom:.6rem}
.hud-world-name{font-size:.92rem;font-weight:850;margin-bottom:.12rem}
.hud-world-topic{font-size:.70rem;opacity:.66}
.hud-stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:.4rem;margin-bottom:.55rem}
.hud-mini-stat{display:flex;justify-content:space-between;align-items:center;padding:.48rem .55rem;border-radius:10px;background:rgba(110,120,160,.045);border:1px solid rgba(120,120,140,.11);font-size:.72rem}
.hud-mini-stat b{font-size:.82rem}
[data-testid="stSidebar"] hr{margin:.75rem 0}
[data-testid="stSidebar"] .stButton button{border-radius:10px;min-height:2.25rem;font-size:.75rem}
[data-testid="stSidebar"] [data-testid="stSelectbox"] label{font-size:.72rem;font-weight:700}

/* ACTIONS help button: Streamlit 기본 popover 화살표 없이 hover 설명만 표시 */
[data-testid="stSidebar"] .action-help-anchor + div button,
[data-testid="stSidebar"] button[aria-label="action help"]{
    min-width:2.25rem!important;
    width:2.25rem!important;
    padding-left:0!important;
    padding-right:0!important;
    justify-content:center!important;
    font-weight:800!important;
}

/* Learning World */
.world-hero{padding:1.35rem 1.45rem;border:1px solid rgba(88,118,190,.20);border-radius:20px;background:linear-gradient(145deg,rgba(91,111,201,.10),rgba(55,180,130,.045));box-shadow:0 10px 28px rgba(20,25,50,.045);margin:.5rem 0 1rem}
.world-hero-top{display:flex;justify-content:space-between;gap:1rem;align-items:flex-start;margin-bottom:.9rem}
.world-eyebrow{font-size:.70rem;letter-spacing:.10em;font-weight:850;opacity:.56;margin-bottom:.22rem}
.world-name{font-size:1.45rem;font-weight:900;line-height:1.2;margin-bottom:.22rem}
.world-meta{font-size:.83rem;opacity:.72}
.world-badge{display:inline-flex;align-items:center;gap:.28rem;padding:.34rem .58rem;border-radius:999px;font-size:.68rem;font-weight:850;border:1px solid rgba(47,150,110,.23);background:rgba(47,180,120,.08);white-space:nowrap}
.world-goal{padding:.78rem .9rem;border-radius:13px;background:rgba(255,255,255,.38);border:1px solid rgba(120,120,140,.12);font-size:.80rem;line-height:1.55;margin-bottom:.78rem}
.world-description{font-size:.82rem;line-height:1.65;opacity:.78;margin-bottom:.9rem}
.world-content-strip{display:flex;align-items:center;justify-content:space-around;gap:.7rem;padding:.78rem .9rem;border-radius:13px;background:rgba(255,255,255,.34);border:1px solid rgba(120,120,140,.12);margin-top:.15rem}
.world-content-item{display:flex;align-items:center;gap:.34rem;white-space:nowrap;font-size:.76rem;opacity:.78}
.world-content-item b{font-size:.96rem;opacity:1;color:var(--text-color)}
.world-nav-card{padding:.78rem .9rem .66rem;border:1px solid rgba(120,120,140,.16);border-radius:15px;background:rgba(255,255,255,.30);min-height:92px;margin-bottom:.45rem}
.world-nav-title{font-size:.88rem;font-weight:850;margin-bottom:.16rem}
.world-nav-copy{font-size:.69rem;opacity:.62;line-height:1.45}
.world-create-head{margin-bottom:.25rem}
.world-create-eyebrow{font-size:.70rem;letter-spacing:.10em;font-weight:850;opacity:.56}
.world-create-title{font-size:1.05rem;font-weight:900;margin:.08rem 0 .15rem}
.world-create-copy{font-size:.73rem;opacity:.66;line-height:1.5}
@media (max-width:700px){.world-content-strip{align-items:flex-start;flex-direction:column;gap:.35rem}}

/* Quest */
.quest-page-head{margin:.15rem 0 .9rem}
.quest-page-eyebrow{font-size:.70rem;letter-spacing:.10em;font-weight:850;opacity:.56;margin-bottom:.18rem}
.quest-page-title{font-size:1.35rem;font-weight:900;line-height:1.22;margin-bottom:.20rem}
.quest-page-copy{font-size:.76rem;opacity:.66;line-height:1.5}
.quest-recommend{padding:.72rem .86rem;border:1px solid rgba(120,120,140,.16);border-radius:15px;background:linear-gradient(145deg,rgba(255,193,79,.075),rgba(110,120,210,.035));margin:.35rem 0 .35rem}
.quest-recommend-top{display:flex;align-items:center;justify-content:space-between;gap:.65rem;margin-bottom:.35rem}
.quest-recommend-eyebrow{font-size:.61rem;letter-spacing:.09em;font-weight:850;opacity:.56;margin-bottom:.07rem}
.quest-recommend-title{font-size:.95rem;font-weight:900;line-height:1.2}
.quest-recommend-badge{padding:.22rem .44rem;border-radius:999px;background:rgba(255,180,50,.08);border:1px solid rgba(220,150,30,.18);font-size:.62rem;font-weight:800;white-space:nowrap}
.quest-recommend-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:.34rem;margin:.36rem 0 .28rem}
.quest-recommend-stat{padding:.38rem .50rem;border:1px solid rgba(120,120,140,.10);border-radius:9px;background:rgba(255,255,255,.27)}
.quest-recommend-stat span{display:block;font-size:.57rem;opacity:.56;margin-bottom:.05rem}
.quest-recommend-stat b{font-size:.75rem}
.quest-recommend-reason{font-size:.67rem;line-height:1.4;opacity:.64}
.quest-prep-head{margin-bottom:.25rem}
.quest-prep-eyebrow{font-size:.68rem;letter-spacing:.09em;font-weight:850;opacity:.56;margin-bottom:.10rem}
.quest-prep-title{font-size:1rem;font-weight:900;margin-bottom:.10rem}
.quest-prep-copy{font-size:.71rem;opacity:.64;line-height:1.45}
.quest-card{padding:1.05rem 1.15rem;border:1px solid rgba(100,110,190,.20);border-radius:17px;background:linear-gradient(145deg,rgba(101,111,210,.095),rgba(255,255,255,.18));margin:.9rem 0 .75rem;box-shadow:0 8px 22px rgba(20,25,50,.035)}
.quest-card-connected{margin-bottom:0;border-radius:17px 17px 0 0;border-bottom-color:rgba(100,110,190,.10);box-shadow:none}
.quest-question-box{margin-top:0;border:1px solid rgba(100,110,190,.18);border-top:0;border-left:5px solid #6c7ae0;border-radius:0 0 12px 12px;background:linear-gradient(180deg,rgba(110,120,190,.075),rgba(110,120,190,.045));box-shadow:0 8px 20px rgba(20,25,50,.03)}
.quest-card-top{display:flex;align-items:flex-start;justify-content:space-between;gap:.8rem}
.quest-card-eyebrow{font-size:.65rem;letter-spacing:.10em;font-weight:850;opacity:.56;margin-bottom:.12rem}
.quest-card-title{font-size:1.08rem;font-weight:900;line-height:1.3}
.quest-card-world{font-size:.68rem;opacity:.60;margin-top:.12rem}
.quest-reward-row{display:flex;gap:.38rem;flex-wrap:wrap;margin-top:.65rem}
.quest-chip{display:inline-flex;align-items:center;padding:.29rem .50rem;border:1px solid rgba(120,120,140,.14);border-radius:999px;background:rgba(255,255,255,.38);font-size:.67rem;font-weight:750}
@media (max-width:700px){.quest-recommend-stats{grid-template-columns:1fr}.quest-card-top,.quest-recommend-top{flex-direction:column}}

/* Dungeon / Adventure UI */
.battle-ready-card{
    padding:1.18rem 1.25rem;
    border:1px solid rgba(120,120,150,.18);
    border-radius:16px;
    background:linear-gradient(145deg,rgba(110,120,180,.07),rgba(255,255,255,.18));
    margin:.55rem 0 .55rem;
}
.battle-ready-eyebrow{font-size:.66rem;letter-spacing:.10em;font-weight:850;opacity:.56;margin-bottom:.25rem}
.battle-ready-title{font-size:1rem;font-weight:850;margin-bottom:.7rem}
.battle-ready-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:.5rem}
.battle-ready-stat{padding:.58rem .65rem;border:1px solid rgba(120,120,145,.13);border-radius:11px;background:rgba(255,255,255,.34)}
.battle-ready-label{font-size:.65rem;opacity:.6;margin-bottom:.1rem}
.battle-ready-value{font-size:.9rem;font-weight:850}
.battle-ball-line{font-size:.69rem;opacity:.68;margin-top:.55rem}
.hunt-section-head{margin:.5rem 0 .8rem}
.hunt-section-eyebrow{font-size:.66rem;letter-spacing:.09em;font-weight:850;opacity:.55;margin-bottom:.15rem}
.hunt-section-title{font-size:1.18rem;font-weight:900;margin-bottom:.12rem}
.hunt-section-copy{font-size:.76rem;opacity:.66}
.hunt-region-card{min-height:8.7rem;padding:.9rem .95rem;border:1px solid rgba(120,120,145,.17);border-radius:14px;background:rgba(105,115,165,.045);margin-bottom:.42rem}
.hunt-region-title{font-size:.95rem;font-weight:900;margin-bottom:.3rem}
.hunt-region-subject{font-size:.72rem;font-weight:750;opacity:.76;margin-bottom:.25rem}
.hunt-region-meta{font-size:.69rem;opacity:.65;margin-bottom:.4rem}
.hunt-region-desc{font-size:.72rem;line-height:1.48;opacity:.72;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
@media (max-width:800px){.battle-ready-grid{grid-template-columns:repeat(2,1fr)}}


/* Active Battle UI */
.battle-stage-head{margin:.15rem 0 .7rem}
.battle-stage-eyebrow{font-size:.66rem;letter-spacing:.10em;font-weight:850;opacity:.55;margin-bottom:.12rem}
.battle-stage-title{font-size:1.12rem;font-weight:900;margin-bottom:.12rem}
.battle-stage-copy{font-size:.72rem;opacity:.64}
.combat-card{padding:1.18rem 1.25rem;border:1px solid rgba(120,120,145,.17);border-radius:17px;background:linear-gradient(145deg,rgba(255,255,255,.28),rgba(105,115,175,.055));min-height:12.4rem;box-shadow:0 7px 20px rgba(20,25,50,.025)}
.combat-card.monster{background:linear-gradient(145deg,rgba(118,91,170,.075),rgba(255,255,255,.24))}
.combat-eyebrow{font-size:.61rem;letter-spacing:.09em;font-weight:850;opacity:.54;margin-bottom:.14rem}
.combat-name{font-size:1.08rem;font-weight:900;line-height:1.3;margin-bottom:.12rem}
.combat-meta{font-size:.69rem;opacity:.63;margin-bottom:.72rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.combat-hp-row{display:flex;justify-content:space-between;align-items:center;font-size:.72rem;margin-bottom:.28rem}
.combat-hp-row b{font-size:.82rem}
.combat-hp-track{height:9px;background:rgba(120,120,140,.13);border-radius:999px;overflow:hidden;margin-bottom:.72rem}
.combat-hp-fill-player{height:100%;border-radius:999px;background:linear-gradient(90deg,#32a4ff,#5b73f2)}
.combat-hp-fill-monster{height:100%;border-radius:999px;background:linear-gradient(90deg,#9b6bde,#6650b8)}
.combat-stat-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:.38rem}
.combat-stat{padding:.48rem .55rem;border:1px solid rgba(120,120,145,.11);border-radius:10px;background:rgba(255,255,255,.28)}
.combat-stat span{display:block;font-size:.59rem;opacity:.55;margin-bottom:.04rem}
.combat-stat b{font-size:.78rem}
.combat-monster-copy{font-size:.68rem;opacity:.66;line-height:1.45;margin-top:.55rem;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.combat-capture{display:inline-flex;margin-top:.55rem;padding:.25rem .48rem;border-radius:999px;border:1px solid rgba(105,82,170,.18);background:rgba(111,86,185,.06);font-size:.64rem;font-weight:800}
.combat-actions-label{font-size:.66rem;letter-spacing:.10em;font-weight:850;opacity:.58;margin:.78rem 0 .38rem}
.combat-ball-note{font-size:.68rem;opacity:.62;padding-top:1.82rem;line-height:1.45}
.combat-log{padding:.62rem .78rem;border:1px solid rgba(120,120,145,.14);border-radius:13px;background:rgba(105,115,165,.035);margin-top:.68rem}
.combat-log-title{font-size:.70rem;font-weight:900;margin-bottom:.28rem}
.combat-log-line{font-size:.70rem;line-height:1.42;padding:.09rem 0;border-bottom:1px solid rgba(120,120,145,.07)}
.combat-log-line:last-child{border-bottom:0}
@media (max-width:800px){.combat-card{min-height:auto}.combat-stat-grid{grid-template-columns:1fr 1fr}}


/* Inventory */
.inventory-head{margin:.15rem 0 .8rem}
.inventory-eyebrow{font-size:.68rem;letter-spacing:.10em;font-weight:850;opacity:.56;margin-bottom:.12rem}
.inventory-title{font-size:1.22rem;font-weight:900;margin-bottom:.14rem}
.inventory-copy{font-size:.74rem;opacity:.66;line-height:1.5}
.equip-slot-card{min-height:8.2rem;padding:.78rem .72rem;border:1px solid rgba(120,120,145,.16);border-radius:14px;background:linear-gradient(145deg,rgba(105,115,175,.055),rgba(255,255,255,.22));margin-bottom:.38rem}
.equip-slot-label{font-size:.66rem;letter-spacing:.07em;font-weight:850;opacity:.58;margin-bottom:.28rem}
.equip-slot-name{font-size:.88rem;font-weight:900;line-height:1.3;margin-bottom:.20rem}
.equip-slot-meta{font-size:.65rem;opacity:.62;line-height:1.4}
.item-card{min-height:9.7rem;padding:.88rem .92rem;border:1px solid rgba(120,120,145,.16);border-radius:14px;background:rgba(255,255,255,.24);margin:.28rem 0 .38rem}
.item-card-top{display:flex;justify-content:space-between;gap:.5rem;align-items:flex-start;margin-bottom:.42rem}
.item-name{font-size:.92rem;font-weight:900;line-height:1.3}
.item-badge{font-size:.60rem;font-weight:800;padding:.20rem .38rem;border-radius:999px;border:1px solid rgba(120,120,145,.14);background:rgba(110,120,180,.05);white-space:nowrap}
.item-meta{font-size:.66rem;opacity:.64;line-height:1.45;margin-bottom:.5rem}
.item-stats{display:flex;gap:.7rem;font-size:.74rem;font-weight:800}
.item-equipped{margin-top:.45rem;font-size:.63rem;font-weight:850;opacity:.72}
.item-compare{margin-top:.48rem;padding:.42rem .5rem;border-radius:9px;background:rgba(110,120,170,.045);font-size:.64rem;line-height:1.45}
.item-compare-title{opacity:.58;margin-bottom:.12rem}
.item-compare-values{display:flex;gap:.65rem;font-weight:850;flex-wrap:wrap}
.item-compare-positive{color:#168a58}
.item-compare-negative{color:#c24d5a}
.item-compare-neutral{opacity:.58}
.bulk-enhance-note{font-size:.68rem;opacity:.62;line-height:1.45;padding-top:.35rem}
.inventory-summary{display:grid;grid-template-columns:repeat(3,1fr);gap:.45rem;margin:.3rem 0 .75rem}
.inventory-summary-card{padding:.62rem .7rem;border:1px solid rgba(120,120,145,.13);border-radius:11px;background:rgba(110,120,170,.04)}
.inventory-summary-label{font-size:.62rem;opacity:.58;margin-bottom:.07rem}
.inventory-summary-value{font-size:.88rem;font-weight:900}
.enhance-card{min-height:10.4rem;padding:.88rem .92rem;border:1px solid rgba(120,120,145,.16);border-radius:14px;background:linear-gradient(145deg,rgba(255,185,75,.045),rgba(255,255,255,.20));margin:.28rem 0 .38rem}
.enhance-title-row{display:flex;align-items:center;gap:.38rem;margin:.12rem 0 .58rem}
.enhance-title-text{font-size:1.18rem;font-weight:900}
.enhance-subtitle-row{display:flex;align-items:center;gap:.32rem;margin:.12rem 0 .42rem}
.enhance-subtitle-text{font-size:.78rem;font-weight:850;letter-spacing:.02em}
.help-dot{display:inline-flex;align-items:center;justify-content:center;width:1.15rem;height:1.15rem;border-radius:999px;border:1px solid rgba(110,115,135,.25);background:rgba(255,255,255,.72);font-size:.66rem;font-weight:900;line-height:1;cursor:help;opacity:.72;vertical-align:middle}
.help-dot:hover{opacity:1;background:rgba(110,120,180,.08)}
.enhance-card{min-height:8.2rem}
.enhance-preview{margin-top:.45rem;padding:.42rem .5rem;border-radius:9px;background:rgba(110,120,170,.045);font-size:.66rem;line-height:1.5}
.consumable-card{padding:.85rem .9rem;border:1px solid rgba(120,120,145,.15);border-radius:14px;background:rgba(255,255,255,.24);min-height:7.6rem}
.consumable-name{font-size:.86rem;font-weight:900;margin-bottom:.22rem}
.consumable-count{font-size:1.35rem;font-weight:900;margin-bottom:.14rem}
.consumable-meta{font-size:.65rem;opacity:.62}
@media (max-width:800px){.inventory-summary{grid-template-columns:1fr}.equip-slot-card{min-height:auto}}



/* WORLD GATE / Onboarding */
.gate-hero{padding:1.15rem 1.25rem;margin:.35rem 0 .7rem;border:1px solid rgba(92,101,170,.18);border-radius:20px;background:linear-gradient(145deg,rgba(84,94,165,.10),rgba(255,255,255,.25));box-shadow:0 12px 30px rgba(25,30,65,.035)}
.gate-eyebrow{font-size:.66rem;letter-spacing:.15em;font-weight:900;opacity:.55;margin-bottom:.18rem}
.gate-title{font-size:1.55rem;font-weight:950;line-height:1.2;margin-bottom:.22rem}.gate-title.small{font-size:1.2rem}
.gate-copy{font-size:.76rem;opacity:.66;line-height:1.5}.gate-player-line{font-size:.75rem;opacity:.72;margin:.2rem 0 1rem}
.gate-choice-card{min-height:11rem;padding:1.2rem 1.25rem;border:1px solid rgba(100,105,160,.16);border-radius:18px;background:linear-gradient(145deg,rgba(100,110,175,.07),rgba(255,255,255,.22));margin-bottom:.45rem}
.gate-choice-card.new-world{background:linear-gradient(145deg,rgba(142,96,190,.075),rgba(255,255,255,.22))}
.gate-choice-icon{font-size:1.6rem;margin-bottom:.55rem}.gate-choice-title{font-size:1.08rem;font-weight:950;margin-bottom:.3rem}.gate-choice-copy{font-size:.73rem;line-height:1.55;opacity:.65}
.gate-empty-card{padding:1.3rem;border:1px dashed rgba(100,105,160,.25);border-radius:18px;text-align:center;background:rgba(100,110,175,.035);margin:.8rem 0}
.gate-world-preview{padding:1rem 1.1rem;border:1px solid rgba(100,105,160,.16);border-radius:17px;background:rgba(100,110,175,.045);margin:.65rem 0 .8rem}
.gate-world-name{font-size:1.08rem;font-weight:950;margin:.12rem 0}.gate-world-meta{font-size:.7rem;opacity:.62}.gate-world-goal,.gate-world-boss{font-size:.72rem;margin-top:.55rem;line-height:1.45}
.gate-loading-shell{max-width:760px;margin:3rem auto .7rem;padding:1.1rem 1.2rem;text-align:center}.gate-loading-text{max-width:760px;margin:0 auto;padding:1.3rem 1.4rem;border:1px solid rgba(100,105,160,.15);border-radius:17px;background:rgba(100,110,175,.04);line-height:2;font-size:.88rem}
.creation-scene{padding:1.25rem 1.35rem;margin:.5rem 0 .85rem;border:1px solid rgba(110,92,165,.18);border-radius:19px;background:radial-gradient(circle at 85% 15%,rgba(153,105,205,.10),transparent 35%),linear-gradient(145deg,rgba(80,88,145,.08),rgba(255,255,255,.22))}
.creation-step{font-size:.63rem;letter-spacing:.13em;font-weight:900;opacity:.52;margin-bottom:.45rem}.creation-oracle{font-size:1.07rem;font-weight:900;line-height:1.55;margin-bottom:.35rem}.creation-sub{font-size:.72rem;opacity:.63;line-height:1.5}
.creation-summary{display:grid;grid-template-columns:1fr 1fr;gap:.55rem;margin:.8rem 0}.creation-summary>div{padding:.7rem .75rem;border:1px solid rgba(100,105,160,.13);border-radius:12px;background:rgba(255,255,255,.24)}.creation-summary span{display:block;font-size:.61rem;opacity:.55;margin-bottom:.12rem}.creation-summary b{font-size:.76rem;line-height:1.4}
.intro-shell{text-align:center;padding:1.2rem;margin:1.5rem auto .8rem;max-width:850px}.intro-title{font-size:1.5rem;font-weight:950;margin:.2rem 0}.intro-copy{font-size:.75rem;opacity:.62}.intro-story{max-width:850px;margin:.3rem auto 1rem;padding:1.5rem 1.65rem;border:1px solid rgba(108,94,170,.19);border-radius:18px;background:radial-gradient(circle at 50% 0%,rgba(129,95,190,.08),transparent 42%),rgba(100,110,175,.035);line-height:2.05;font-size:.94rem}
@media(max-width:800px){.creation-summary{grid-template-columns:1fr}.gate-choice-card{min-height:auto}}


/* =========================================================
   CINEMATIC PORTAL MODE
   로그인 / 월드 게이트 / 생성 / 인트로에서만 활성화
   ========================================================= */
.portal-mode-marker{display:none}
.stApp:has(.portal-mode-marker){
    background:
      radial-gradient(circle at 50% -5%, rgba(25,226,255,.22), transparent 27%),
      radial-gradient(circle at 8% 82%, rgba(0,128,255,.18), transparent 26%),
      radial-gradient(circle at 90% 72%, rgba(66,77,255,.18), transparent 28%),
      repeating-linear-gradient(90deg, rgba(47,210,255,.025) 0 1px, transparent 1px 58px),
      repeating-linear-gradient(0deg, rgba(47,210,255,.022) 0 1px, transparent 1px 58px),
      linear-gradient(180deg,#031321 0%,#061c31 48%,#03111f 100%) !important;
    color:#edfaff;
    min-height:100vh;
}
.stApp:has(.portal-mode-marker)::before{
    content:"";position:fixed;inset:0;pointer-events:none;z-index:0;
    background:
      radial-gradient(circle at 15% 18%,rgba(255,255,255,.55) 0 1px,transparent 1.7px),
      radial-gradient(circle at 76% 27%,rgba(111,231,255,.55) 0 1px,transparent 1.8px),
      radial-gradient(circle at 33% 72%,rgba(255,255,255,.35) 0 1px,transparent 1.7px),
      radial-gradient(circle at 88% 78%,rgba(111,231,255,.45) 0 1px,transparent 1.9px);
    background-size:240px 220px,310px 280px,270px 260px,350px 300px;
    opacity:.6;
}
.stApp:has(.portal-mode-marker) .block-container{max-width:980px;padding-top:5vh;padding-bottom:5vh;position:relative;z-index:1}
.stApp:has(.portal-mode-marker) header[data-testid="stHeader"]{background:transparent}
.stApp:has(.portal-mode-marker) [data-testid="stSidebar"]{display:none}
.stApp:has(.portal-mode-marker) h1,.stApp:has(.portal-mode-marker) h2,.stApp:has(.portal-mode-marker) h3,
.stApp:has(.portal-mode-marker) p,.stApp:has(.portal-mode-marker) label,.stApp:has(.portal-mode-marker) .stCaption{color:#eafaff !important}

.portal-hud-frame,.portal-login-head,.portal-oracle-panel{
    position:relative;margin:1.2rem auto 1.35rem;padding:1.45rem 1.65rem;
    border:1px solid rgba(96,226,255,.58);border-radius:6px;
    background:linear-gradient(180deg,rgba(8,39,63,.84),rgba(6,28,49,.75));
    box-shadow:0 0 0 1px rgba(52,185,255,.13) inset,0 0 28px rgba(0,190,255,.10),0 18px 50px rgba(0,0,0,.28);
    overflow:hidden;
}
.portal-hud-frame:before,.portal-login-head:before,.portal-oracle-panel:before{
    content:"";position:absolute;left:0;top:0;width:34%;height:3px;
    background:linear-gradient(90deg,#50ecff,rgba(80,236,255,0));box-shadow:0 0 14px #32dfff;
}
.portal-kicker,.portal-sequence-kicker{font-size:.68rem;letter-spacing:.22em;font-weight:900;color:#72eaff;text-shadow:0 0 12px rgba(80,234,255,.45)}
.portal-gate-title,.portal-login-title{font-size:2rem;font-weight:950;margin:.28rem 0 .34rem;color:#f5fdff;text-shadow:0 0 15px rgba(112,229,255,.18)}
.portal-gate-copy,.portal-login-copy{font-size:.84rem;color:rgba(224,247,255,.72);line-height:1.6}
.portal-sequence-kicker{text-align:center;margin:8vh auto 1rem}
.portal-cinematic-line{
    min-height:42vh;display:flex;align-items:center;justify-content:center;text-align:center;
    padding:2rem 3rem;font-size:clamp(1.65rem,3.4vw,3rem);font-weight:850;line-height:1.55;
    color:#f6fdff;text-shadow:0 0 10px rgba(100,226,255,.78),0 0 28px rgba(0,126,255,.48);
    animation:portalSentence 1.35s ease both;
}
.portal-blank{animation:none;opacity:0}
@keyframes portalSentence{0%{opacity:0;transform:translateY(8px);filter:blur(3px)}18%{opacity:1;transform:none;filter:none}78%{opacity:1}100%{opacity:.10;filter:blur(1px)}}
.portal-intro-ready{min-height:34vh;display:flex;align-items:center;justify-content:center;text-align:center;font-size:1.45rem;font-weight:800;color:rgba(234,250,255,.84);text-shadow:0 0 16px rgba(58,208,255,.30)}
.portal-oracle-question{font-size:clamp(1.35rem,2.5vw,2rem);font-weight:900;line-height:1.55;color:#f6fdff;margin:.35rem 0 .48rem;text-shadow:0 0 13px rgba(94,222,255,.22)}
.portal-oracle-sub{font-size:.82rem;color:rgba(223,246,255,.68);line-height:1.55}
.stApp:has(.portal-mode-marker) [data-testid="stTextInput"] input,
.stApp:has(.portal-mode-marker) [data-testid="stTextArea"] textarea,
.stApp:has(.portal-mode-marker) [data-testid="stSelectbox"] div[data-baseweb="select"]>div{
    background:rgba(4,27,47,.82)!important;border:1px solid rgba(87,219,255,.34)!important;color:#eefcff!important;
    border-radius:7px!important;box-shadow:0 0 0 1px rgba(26,163,220,.05) inset;
}
/* Login/player selector visibility ------------------------------------------------ */
/* Streamlit/BaseWeb changed its select DOM between versions.  Paint every control
   layer instead of only the first child so the login selector cannot fall back to
   Streamlit's white surface. */
.stApp:has(.portal-mode-marker) [data-testid="stSelectbox"] div[data-baseweb="select"],
.stApp:has(.portal-mode-marker) [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
.stApp:has(.portal-mode-marker) [data-testid="stSelectbox"] div[data-baseweb="select"] > div > div{
    background-color:#08243a!important;
    background:#08243a!important;
    border-color:rgba(95,224,255,.55)!important;
}
.stApp:has(.portal-mode-marker) [data-testid="stSelectbox"] div[data-baseweb="select"] > div{
    background:#08243a!important;
    border:1px solid rgba(95,224,255,.55)!important;
    color:#f4fdff!important;
}
.stApp:has(.portal-mode-marker) [data-testid="stSelectbox"] div[data-baseweb="select"] span,
.stApp:has(.portal-mode-marker) [data-testid="stSelectbox"] div[data-baseweb="select"] div,
.stApp:has(.portal-mode-marker) [data-testid="stSelectbox"] [data-testid="stMarkdownContainer"] p{
    color:#f4fdff!important;
    -webkit-text-fill-color:#f4fdff!important;
    opacity:1!important;
}
.stApp:has(.portal-mode-marker) [data-testid="stSelectbox"] svg{
    fill:#bcefff!important;
    color:#bcefff!important;
}
/* BaseWeb dropdown menu is rendered in a portal outside .stApp. Keep options readable
   even when Streamlit chooses a white popover surface. */
body:has(.portal-mode-marker) div[data-baseweb="popover"] ul,
body:has(.portal-mode-marker) div[data-baseweb="menu"]{
    background:#08243a!important;
}
body:has(.portal-mode-marker) div[data-baseweb="popover"] li,
body:has(.portal-mode-marker) div[data-baseweb="menu"] li{
    color:#f4fdff!important;
    -webkit-text-fill-color:#f4fdff!important;
}
body:has(.portal-mode-marker) div[data-baseweb="popover"] li:hover,
body:has(.portal-mode-marker) div[data-baseweb="menu"] li:hover{
    background:#0d3857!important;
}
.stApp:has(.portal-mode-marker) input,.stApp:has(.portal-mode-marker) textarea{color:#eefcff!important}
.stApp:has(.portal-mode-marker) button[kind="primary"],.stApp:has(.portal-mode-marker) .stButton>button[kind="primary"]{
    background:linear-gradient(90deg,#0878c8,#05b8dc)!important;border:1px solid rgba(111,235,255,.65)!important;color:white!important;
    box-shadow:0 0 20px rgba(0,183,255,.18)!important;
}
.stApp:has(.portal-mode-marker) .stButton>button{
    border-color:rgba(104,218,255,.30)!important;background:rgba(5,33,54,.68)!important;color:#eafaff!important;
}
.stApp:has(.portal-mode-marker) [data-testid="stExpander"]{background:rgba(5,31,52,.62);border-color:rgba(86,214,255,.24)}
.stApp:has(.portal-mode-marker) [data-testid="stAlert"]{background:rgba(7,39,61,.82);color:#eafaff;border-color:rgba(95,220,255,.28)}
.stApp:has(.portal-mode-marker) .gate-choice-card,.stApp:has(.portal-mode-marker) .gate-empty-card,.stApp:has(.portal-mode-marker) .gate-world-preview,
.stApp:has(.portal-mode-marker) .creation-summary>div{
    background:linear-gradient(180deg,rgba(8,43,69,.76),rgba(4,29,49,.70));border-color:rgba(91,220,255,.32);color:#eefcff;
    box-shadow:0 0 22px rgba(0,180,255,.06) inset;
}
.stApp:has(.portal-mode-marker) .gate-choice-title,.stApp:has(.portal-mode-marker) .gate-world-name,.stApp:has(.portal-mode-marker) .creation-summary b{color:#f4fdff}
.stApp:has(.portal-mode-marker) .gate-choice-copy,.stApp:has(.portal-mode-marker) .gate-world-meta,.stApp:has(.portal-mode-marker) .gate-world-goal,.stApp:has(.portal-mode-marker) .gate-world-boss,
.stApp:has(.portal-mode-marker) .gate-player-line{color:rgba(224,247,255,.70)}
@media(max-width:800px){.portal-cinematic-line{min-height:38vh;padding:1.3rem .8rem;font-size:1.65rem}.portal-gate-title,.portal-login-title{font-size:1.65rem}}



/* LOGIN SELECTBOX v5 ----------------------------------------------------------
   Streamlit 1.5x may paint the visible surface on the combobox input itself.
   Cover the control, combobox input and focus layer explicitly. */
.stApp:has(.portal-mode-marker) [data-testid="stSelectbox"] div[data-baseweb="select"],
.stApp:has(.portal-mode-marker) [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
.stApp:has(.portal-mode-marker) [data-testid="stSelectbox"] [role="combobox"],
.stApp:has(.portal-mode-marker) [data-testid="stSelectbox"] input[role="combobox"] {
    background:#08243a !important;
    background-color:#08243a !important;
    color:#f4fdff !important;
    -webkit-text-fill-color:#f4fdff !important;
    caret-color:#72eaff !important;
}
.stApp:has(.portal-mode-marker) [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    border:1px solid rgba(95,224,255,.62) !important;
    box-shadow:0 0 0 1px rgba(65,205,255,.07) inset,0 0 16px rgba(0,190,255,.06) !important;
}
.stApp:has(.portal-mode-marker) [data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within > div,
.stApp:has(.portal-mode-marker) [data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within {
    background:#0a2b45 !important;
    border-color:#62e5ff !important;
    box-shadow:0 0 0 1px #62e5ff inset,0 0 18px rgba(65,214,255,.16) !important;
}
.stApp:has(.portal-mode-marker) [data-testid="stSelectbox"] input[role="combobox"]::placeholder {
    color:rgba(224,248,255,.48) !important;
    -webkit-text-fill-color:rgba(224,248,255,.48) !important;
}
/* Some Streamlit releases put the selected value in a sibling div rather than input. */
.stApp:has(.portal-mode-marker) [data-testid="stSelectbox"] div[data-baseweb="select"] [aria-selected],
.stApp:has(.portal-mode-marker) [data-testid="stSelectbox"] div[data-baseweb="select"] span {
    color:#f4fdff !important;
    -webkit-text-fill-color:#f4fdff !important;
}

/* =====================================================================
   VILLAGE HUB v6 - LIGHTWEIGHT CARD CAROUSEL
   Old grid/map/road/scene CSS has been removed.
   ===================================================================== */
.stApp:has(.hub6-mode-marker){
    background:
      radial-gradient(circle at 20% 8%,rgba(52,180,212,.14),transparent 34%),
      radial-gradient(circle at 82% 60%,rgba(52,94,220,.10),transparent 30%),
      linear-gradient(180deg,#071e30 0%,#0a2938 60%,#071d2a 100%)!important;
    color:#edfaff;
    min-height:100vh;
}
.stApp:has(.hub6-mode-marker) .block-container{
    position:relative;
    z-index:1;
    max-width:1180px!important;
    padding-top:1.1rem;
}
.stApp:has(.hub6-mode-marker) h1,
.stApp:has(.hub6-mode-marker) h2,
.stApp:has(.hub6-mode-marker) h3,
.stApp:has(.hub6-mode-marker) p,
.stApp:has(.hub6-mode-marker) label{
    color:#eefcff!important;
}
.stApp:has(.hub6-mode-marker) .stButton>button{
    min-height:2.55rem;
    background:rgba(7,39,62,.82)!important;
    border-color:rgba(96,221,255,.28)!important;
    color:#f1fcff!important;
}
.stApp:has(.hub6-mode-marker) .stButton>button[kind="primary"]{
    background:linear-gradient(90deg,#0878c8,#06bddb)!important;
    border-color:rgba(109,233,255,.64)!important;
}

.hub6-account{
    min-height:2.55rem;
    display:flex;align-items:center;gap:.55rem;
    padding:.5rem .75rem;margin-bottom:.48rem;
    border-radius:11px;
    border:1px solid rgba(89,220,255,.18);
    background:rgba(4,31,51,.62);
    color:rgba(230,249,255,.72);
    font-size:.68rem;
}
.hub6-account b{color:#f5fdff;font-size:.78rem}
.hub6-dot{
    width:7px;height:7px;border-radius:50%;
    background:#58edff;box-shadow:0 0 10px rgba(88,237,255,.9);
}
.hub6-key-help{
    margin-left:auto;color:#79eaff;font-size:.61rem;font-weight:850;
}

.hub6-world-current{
    min-height:3.25rem;
    padding:.58rem .75rem;margin:.15rem 0 .7rem;
    border-radius:12px;
    border:1px solid rgba(99,222,255,.18);
    background:linear-gradient(145deg,rgba(11,57,76,.58),rgba(5,34,49,.72));
}
.hub6-world-current-kicker{
    font-size:.51rem;letter-spacing:.16em;font-weight:950;color:#72eaff;
}
.hub6-world-current-name{
    margin-top:.08rem;font-size:.84rem;font-weight:950;color:#f4fdff;
}
.hub6-world-current-meta{
    margin-top:.08rem;font-size:.59rem;color:rgba(226,248,255,.58);
}

.hub6-shell{
    position:relative;
    min-height:760px;
    overflow:hidden;
    border-radius:22px;
    border:1px solid rgba(96,224,255,.30);
    background-size:cover!important;
    background-position:center!important;
    box-shadow:0 18px 48px rgba(0,0,0,.22), inset 0 0 74px rgba(0,0,0,.18);
    padding:1.2rem 1.25rem 1rem;
}
.hub6-shell::before{
    content:"";
    position:absolute;inset:0;pointer-events:none;
    background:
      radial-gradient(ellipse at 50% 53%,rgba(74,220,255,.12),transparent 32%),
      linear-gradient(180deg,rgba(2,18,29,.10),rgba(2,18,29,.68));
}
.hub6-world-kicker{
    position:relative;z-index:10;
    font-size:.62rem;font-weight:950;letter-spacing:.18em;color:#75edff;
}
.hub6-world-name{
    position:relative;z-index:10;
    margin-top:.1rem;
    font-size:1.35rem;font-weight:950;color:#f5fdff;
}

.hub6-stage{
    position:relative;
    height:520px;
    margin-top:.25rem;
    perspective:1300px;
}
.hub6-card{
    position:absolute;
    left:50%;top:49%;
    width:360px;height:480px; /* 3:4 portrait card */
    border-radius:22px;
    border:1px solid rgba(150,233,255,.24);
    background:linear-gradient(165deg,rgba(16,61,82,.96),rgba(4,29,48,.98));
    box-shadow:0 18px 34px rgba(0,0,0,.30);
    overflow:hidden;
    transform-style:preserve-3d;
    transition:transform .22s ease,opacity .22s ease,filter .22s ease;
}
.hub6-card.active{
    z-index:9;
    transform:translate(-50%,-49%) translateZ(95px);
    border-color:rgba(115,235,255,.76);
    box-shadow:0 26px 54px rgba(0,0,0,.40),0 0 34px rgba(54,216,255,.18);
}
.hub6-card.left{
    z-index:6;
    transform:translate(-112%,-46%) rotateY(30deg) rotateZ(-4deg) scale(.76);
    opacity:.68;filter:saturate(.76);
}
.hub6-card.right{
    z-index:6;
    transform:translate(12%,-46%) rotateY(-30deg) rotateZ(4deg) scale(.76);
    opacity:.68;filter:saturate(.76);
}
.hub6-card.far-left{
    z-index:4;
    transform:translate(-160%,-40%) rotateY(40deg) rotateZ(-8deg) scale(.55);
    opacity:.28;filter:saturate(.45);
}
.hub6-card.far-right{
    z-index:4;
    transform:translate(60%,-40%) rotateY(-40deg) rotateZ(8deg) scale(.55);
    opacity:.28;filter:saturate(.45);
}

.hub6-art-wrap{
    height:62%;
    display:flex;align-items:center;justify-content:center;
    background:
      radial-gradient(circle at 50% 54%,rgba(89,226,255,.16),transparent 56%),
      linear-gradient(180deg,rgba(255,255,255,.018),rgba(0,0,0,.08));
}
.hub6-art{
    width:84%;height:86%;object-fit:contain;
    filter:drop-shadow(0 10px 12px rgba(0,0,0,.34));
}
.hub6-fallback{font-size:5rem}
.hub6-card-body{
    height:38%;
    padding:1.18rem 1.25rem;
    background:linear-gradient(180deg,rgba(3,25,40,.30),rgba(3,21,35,.94));
}
.hub6-section{
    font-size:.74rem;font-weight:950;letter-spacing:.15em;color:#73eaff;
}
.hub6-name{
    margin-top:.25rem;
    font-size:1.62rem;font-weight:950;line-height:1.16;color:#f7fdff;
}
.hub6-tagline{
    margin-top:.48rem;
    font-size:.96rem;line-height:1.5;color:rgba(231,249,255,.76);
}
.hub6-card:not(.active) .hub6-tagline{display:none}

.hub6-hint{
    position:relative;z-index:10;
    margin-top:.62rem;text-align:center;
    font-size:.64rem;font-weight:850;letter-spacing:.05em;
    color:rgba(169,240,255,.72);
}
.hub6-help{
    margin-top:.8rem;padding:.78rem .9rem;
    border-radius:12px;border:1px solid rgba(91,219,255,.15);
    background:rgba(4,32,52,.58);
    color:rgba(230,249,255,.68);
    font-size:.7rem;line-height:1.6;
}

@media(max-width:900px){
    .hub6-shell{min-height:600px}
    .hub6-stage{height:375px}
    .hub6-card{width:250px;height:333px}
    .hub6-card.left{transform:translate(-112%,-45%) rotateY(28deg) rotateZ(-4deg) scale(.66)}
    .hub6-card.right{transform:translate(12%,-45%) rotateY(-28deg) rotateZ(4deg) scale(.66)}
    .hub6-card.far-left,.hub6-card.far-right{opacity:.10}
    .hub6-key-help{display:none}
}


.hub6-description{
    margin-top:.72rem;
    padding-top:.68rem;
    border-top:1px solid rgba(120,230,255,.16);
    font-size:.91rem;
    line-height:1.58;
    color:rgba(238,251,255,.78);
}
.hub6-hint-key{
    color:#dffbff;
    font-weight:950;
}
.hub6-hint-sep{
    display:inline-block;
    margin:0 .7rem;
    color:rgba(130,230,255,.36);
}



/* =====================================================================
   VILLAGE HUB v9 - STRONG THEME IDENTITY
   카드 레이아웃은 유지하고, 테마별 배경/색감/장식을 강하게 분리한다.
   ===================================================================== */

/* 공통: 테마 컬러를 CSS 변수로 받는다. */
.hub6-shell{
    --theme-accent:#65e8ff;
    --theme-accent-rgb:101,232,255;
    --theme-card-top:rgba(14,66,88,.98);
    --theme-card-bottom:rgba(4,28,47,.98);
    --theme-stage-glow:rgba(77,220,255,.12);
    --theme-title:#f7fdff;
}
.hub6-shell::after{
    content:"";
    position:absolute;
    inset:0;
    z-index:0;
    pointer-events:none;
    opacity:.9;
}
.hub6-world-kicker,
.hub6-world-name,
.hub6-stage,
.hub6-hint{
    position:relative;
    z-index:3;
}
.hub6-card{
    background:linear-gradient(165deg,var(--theme-card-top),var(--theme-card-bottom))!important;
}
.hub6-card.active{
    border-color:rgba(var(--theme-accent-rgb),.86)!important;
    box-shadow:
      0 28px 58px rgba(0,0,0,.42),
      0 0 38px rgba(var(--theme-accent-rgb),.22)!important;
}
.hub6-section{
    color:var(--theme-accent)!important;
}
.hub6-name,
.hub6-world-name{
    color:var(--theme-title)!important;
}
.hub6-art-wrap{
    background:
      radial-gradient(circle at 50% 55%,rgba(var(--theme-accent-rgb),.20),transparent 58%),
      linear-gradient(180deg,rgba(255,255,255,.025),rgba(0,0,0,.10))!important;
}
.hub6-hint-key{
    color:var(--theme-accent)!important;
}

/* ---------- 판타지 ---------- */
.hub6-shell.theme-fantasy{
    --theme-accent:#7fe7ff;
    --theme-accent-rgb:127,231,255;
    --theme-card-top:rgba(25,74,112,.98);
    --theme-card-bottom:rgba(8,35,59,.98);
    --theme-title:#f6fbff;
    background-color:#16365a!important;
    background-blend-mode:soft-light,normal!important;
}
.hub6-shell.theme-fantasy::before{
    background:
      radial-gradient(circle at 18% 16%,rgba(255,239,170,.30) 0 7%,transparent 7.5%),
      radial-gradient(circle at 82% 24%,rgba(111,225,255,.17),transparent 19%),
      linear-gradient(180deg,rgba(20,45,84,.08),rgba(14,51,83,.18) 44%,rgba(36,92,69,.42) 75%,rgba(25,67,50,.60))!important;
}
.hub6-shell.theme-fantasy::after{
    background:
      radial-gradient(ellipse at 50% 89%,rgba(90,158,84,.30),transparent 38%),
      linear-gradient(120deg,transparent 0 26%,rgba(101,216,255,.04) 26% 27%,transparent 27% 100%);
}

/* ---------- 무협 ---------- */
.hub6-shell.theme-murim{
    --theme-accent:#f3c96b;
    --theme-accent-rgb:243,201,107;
    --theme-card-top:rgba(72,53,43,.98);
    --theme-card-bottom:rgba(28,27,31,.99);
    --theme-title:#fff3cf;
    background-color:#79644b!important;
    background-blend-mode:multiply,normal!important;
}
.hub6-shell.theme-murim::before{
    background:
      radial-gradient(circle at 84% 18%,rgba(255,222,139,.44) 0 9%,transparent 9.5%),
      linear-gradient(180deg,rgba(210,188,147,.16),rgba(129,108,79,.26) 44%,rgba(69,79,63,.56) 75%,rgba(41,48,40,.72))!important;
}
.hub6-shell.theme-murim::after{
    background:
      linear-gradient(160deg,transparent 0 52%,rgba(28,34,31,.60) 52% 65%,transparent 65%),
      linear-gradient(20deg,transparent 0 58%,rgba(41,51,45,.52) 58% 71%,transparent 71%),
      radial-gradient(ellipse at 34% 78%,rgba(235,230,211,.12),transparent 34%);
}
.hub6-shell.theme-murim .hub6-card{
    border-color:rgba(243,201,107,.24)!important;
}
.hub6-shell.theme-murim .hub6-card.active{
    border-color:rgba(243,201,107,.88)!important;
}

/* ---------- SF ---------- */
.hub6-shell.theme-sf{
    --theme-accent:#48f4ff;
    --theme-accent-rgb:72,244,255;
    --theme-card-top:rgba(16,61,98,.98);
    --theme-card-bottom:rgba(4,17,37,.99);
    --theme-title:#ecfeff;
    background-color:#03172c!important;
    background-blend-mode:screen,normal!important;
}
.hub6-shell.theme-sf::before{
    background:
      radial-gradient(circle at 82% 14%,rgba(83,109,255,.24) 0 12%,transparent 12.5%),
      radial-gradient(circle at 18% 33%,rgba(178,96,255,.16),transparent 18%),
      linear-gradient(180deg,rgba(0,12,33,.20),rgba(2,17,41,.64))!important;
}
.hub6-shell.theme-sf::after{
    opacity:.8;
    background:
      repeating-linear-gradient(90deg,rgba(73,238,255,.055) 0 1px,transparent 1px 56px),
      repeating-linear-gradient(0deg,rgba(73,238,255,.045) 0 1px,transparent 1px 56px),
      linear-gradient(135deg,transparent 0 45%,rgba(142,89,255,.09) 45% 47%,transparent 47% 100%);
}
.hub6-shell.theme-sf .hub6-card.active{
    box-shadow:
      0 28px 58px rgba(0,0,0,.44),
      0 0 30px rgba(72,244,255,.28),
      0 0 70px rgba(128,82,255,.12)!important;
}

/* ---------- 현대 ---------- */
.hub6-shell.theme-modern{
    --theme-accent:#3ca7ff;
    --theme-accent-rgb:60,167,255;
    --theme-card-top:rgba(55,79,101,.97);
    --theme-card-bottom:rgba(18,35,52,.98);
    --theme-title:#ffffff;
    background-color:#99b9ca!important;
    background-blend-mode:luminosity,normal!important;
}
.hub6-shell.theme-modern::before{
    background:
      linear-gradient(180deg,rgba(220,239,249,.18),rgba(145,175,192,.36) 56%,rgba(79,112,125,.48))!important;
}
.hub6-shell.theme-modern::after{
    opacity:.68;
    background:
      linear-gradient(90deg,
        transparent 0 8%,
        rgba(49,70,83,.26) 8% 14%,
        transparent 14% 18%,
        rgba(61,83,97,.20) 18% 25%,
        transparent 25% 74%,
        rgba(52,73,88,.24) 74% 82%,
        transparent 82% 100%),
      repeating-linear-gradient(0deg,transparent 0 22px,rgba(255,255,255,.035) 22px 23px);
}

/* ---------- 귀여운 몬스터 ---------- */
.hub6-shell.theme-cute{
    --theme-accent:#ff83c5;
    --theme-accent-rgb:255,131,197;
    --theme-card-top:rgba(86,157,191,.97);
    --theme-card-bottom:rgba(71,94,150,.96);
    --theme-title:#fffaff;
    background-color:#8ed8f6!important;
    background-blend-mode:screen,normal!important;
}
.hub6-shell.theme-cute::before{
    background:
      radial-gradient(circle at 18% 18%,rgba(255,255,255,.72) 0 6%,transparent 6.5%),
      radial-gradient(circle at 28% 15%,rgba(255,255,255,.58) 0 4.5%,transparent 5%),
      radial-gradient(circle at 80% 20%,rgba(255,231,246,.52),transparent 13%),
      linear-gradient(180deg,rgba(125,211,255,.12),rgba(255,184,220,.18) 54%,rgba(126,201,116,.52) 78%,rgba(94,173,90,.58))!important;
}
.hub6-shell.theme-cute::after{
    background:
      radial-gradient(circle at 13% 63%,rgba(255,250,162,.18) 0 2%,transparent 2.5%),
      radial-gradient(circle at 87% 60%,rgba(255,255,255,.22) 0 1.5%,transparent 2%),
      radial-gradient(circle at 72% 74%,rgba(255,187,229,.22) 0 2.5%,transparent 3%);
}
.hub6-shell.theme-cute .hub6-card{
    border-color:rgba(255,225,246,.26)!important;
    border-radius:28px!important;
}
.hub6-shell.theme-cute .hub6-card.active{
    border-color:rgba(255,151,211,.90)!important;
}

/* ---------- 다크 판타지 ---------- */
.hub6-shell.theme-dark_fantasy{
    --theme-accent:#ba7cff;
    --theme-accent-rgb:186,124,255;
    --theme-card-top:rgba(58,34,72,.99);
    --theme-card-bottom:rgba(17,12,27,.99);
    --theme-title:#fff2ff;
    background-color:#150d20!important;
    background-blend-mode:multiply,normal!important;
}
.hub6-shell.theme-dark_fantasy::before{
    background:
      radial-gradient(circle at 82% 17%,rgba(160,47,62,.40) 0 8%,transparent 8.5%),
      radial-gradient(circle at 20% 22%,rgba(123,80,184,.15),transparent 17%),
      linear-gradient(180deg,rgba(15,8,26,.32),rgba(20,11,31,.66) 55%,rgba(28,24,31,.84))!important;
}
.hub6-shell.theme-dark_fantasy::after{
    background:
      linear-gradient(160deg,transparent 0 51%,rgba(18,17,22,.72) 51% 67%,transparent 67%),
      radial-gradient(ellipse at 50% 84%,rgba(95,54,112,.18),transparent 34%),
      repeating-linear-gradient(110deg,rgba(255,255,255,.018) 0 1px,transparent 1px 44px);
}
.hub6-shell.theme-dark_fantasy .hub6-card.active{
    box-shadow:
      0 28px 58px rgba(0,0,0,.56),
      0 0 34px rgba(186,124,255,.26),
      0 0 70px rgba(117,37,105,.15)!important;
}

/* ---------- 카드 뒤쪽 톤도 테마에 맞춰 더 확실히 분리 ---------- */
.hub6-shell .hub6-card.left,
.hub6-shell .hub6-card.right{
    opacity:.72;
}
.hub6-shell .hub6-card.far-left,
.hub6-shell .hub6-card.far-right{
    opacity:.30;
}




/* =========================================================
   GAME SHELL / SIDEBAR THEME SYNC v2
   - sidebar만 월드 테마별 변경
   - header는 모든 테마에서 동일한 navy
   - main 화면은 앱 공통 dark theme 사용
   ========================================================= */
.sidebar-theme-marker{display:none}

/* sidebar theme variables --------------------------------------------------- */
.stApp:has(.sidebar-theme-fantasy){
    --side-bg:#151a35;
    --side-bg-soft:#22294b;
    --side-panel:rgba(45,52,94,.92);
    --side-panel-soft:rgba(126,137,218,.13);
    --side-border:rgba(160,170,236,.28);
    --side-accent:#aab3ff;
    --side-accent-2:#c7a8ff;
    --side-text:#f0f1ff;
    --side-muted:#aeb5d7;
}
.stApp:has(.sidebar-theme-wuxia){
    --side-bg:#241716;
    --side-bg-soft:#35211e;
    --side-panel:rgba(69,42,35,.93);
    --side-panel-soft:rgba(179,127,81,.12);
    --side-border:rgba(210,167,105,.28);
    --side-accent:#d5aa69;
    --side-accent-2:#b86f60;
    --side-text:#fff4e9;
    --side-muted:#cfb6a1;
}
.stApp:has(.sidebar-theme-sf){
    --side-bg:#061b2c;
    --side-bg-soft:#082b3d;
    --side-panel:rgba(8,42,62,.94);
    --side-panel-soft:rgba(48,205,229,.10);
    --side-border:rgba(76,220,239,.30);
    --side-accent:#45d8ec;
    --side-accent-2:#628cff;
    --side-text:#eafcff;
    --side-muted:#9ccbd4;
}
.stApp:has(.sidebar-theme-cute){
    --side-bg:#eaf4ff;
    --side-bg-soft:#f4f0ff;
    --side-panel:rgba(248,251,255,.98);
    --side-panel-soft:rgba(111,171,220,.13);
    --side-border:rgba(108,151,198,.28);
    --side-accent:#64add8;
    --side-accent-2:#e4a0c2;
    --side-text:#263950;
    --side-muted:#6f8095;
}
.stApp:has(.sidebar-theme-dark-fantasy){
    --side-bg:#160f21;
    --side-bg-soft:#25162f;
    --side-panel:rgba(42,26,53,.94);
    --side-panel-soft:rgba(171,78,130,.11);
    --side-border:rgba(191,105,158,.28);
    --side-accent:#c46fa7;
    --side-accent-2:#8f68d4;
    --side-text:#f7eef9;
    --side-muted:#bda9c6;
}
.stApp:has(.sidebar-theme-modern){
    --side-bg:#182334;
    --side-bg-soft:#223149;
    --side-panel:rgba(35,49,72,.95);
    --side-panel-soft:rgba(104,143,184,.10);
    --side-border:rgba(111,143,180,.25);
    --side-accent:#75a2cf;
    --side-accent-2:#8fb3d7;
    --side-text:#eff5fb;
    --side-muted:#a7b5c6;
}

/* fixed global header ------------------------------------------------------- */
header[data-testid="stHeader"]{
    background:#11172d !important;
    border-bottom:1px solid rgba(125,145,185,.18) !important;
}
[data-testid="stToolbar"]{
    background:transparent !important;
}
[data-testid="stDecoration"]{
    background:linear-gradient(90deg,#1bbbd0,#6d7df1) !important;
}

/*
Streamlit header는 overlay 방식이라 block-container가 너무 위로 올라오면
'마을로' / 페이지 제목이 헤더 아래에 가려진다.
게임 화면에서는 헤더 높이만큼 안전 여백을 확보한다.
*/
.stApp:has(.sidebar-theme-marker) [data-testid="stMainBlockContainer"],
.stApp:has(.sidebar-theme-marker) section[data-testid="stMain"] .block-container{
    max-width:1520px !important;
    padding-top:3.85rem !important;
    padding-left:1.15rem !important;
    padding-right:1.15rem !important;
    padding-bottom:2rem !important;
}

/* portal/login 화면은 기존 cinematic spacing을 유지 */
.stApp:has(.portal-mode-marker) [data-testid="stMainBlockContainer"],
.stApp:has(.portal-mode-marker) section[data-testid="stMain"] .block-container{
    padding-top:5vh !important;
}

/* sidebar shell ------------------------------------------------------------- */
.stApp:has(.sidebar-theme-marker) section[data-testid="stSidebar"]{
    background:
        radial-gradient(circle at 14% 4%,var(--side-panel-soft),transparent 30%),
        linear-gradient(180deg,var(--side-bg-soft),var(--side-bg)) !important;
    border-right:1px solid var(--side-border) !important;
}

/* 텍스트는 넓은 * 선택자를 쓰지 않고 필요한 UI만 명시한다 */
.stApp:has(.sidebar-theme-marker) .hud-card,
.stApp:has(.sidebar-theme-marker) .hud-world,
.stApp:has(.sidebar-theme-marker) .hud-stat,
.stApp:has(.sidebar-theme-marker) .hud-resource,
.stApp:has(.sidebar-theme-marker) .hud-mini-stat,
.stApp:has(.sidebar-theme-marker) .hud-section-title{
    color:var(--side-text) !important;
}
.stApp:has(.sidebar-theme-marker) .hud-eyebrow,
.stApp:has(.sidebar-theme-marker) .hud-subtitle,
.stApp:has(.sidebar-theme-marker) .hud-xp,
.stApp:has(.sidebar-theme-marker) .hud-stat-label,
.stApp:has(.sidebar-theme-marker) .hud-resource-label,
.stApp:has(.sidebar-theme-marker) .hud-world-topic,
.stApp:has(.sidebar-theme-marker) .hud-section-title{
    color:var(--side-muted) !important;
}

/* HUD cards */
.stApp:has(.sidebar-theme-marker) .hud-card{
    background:linear-gradient(145deg,var(--side-panel),var(--side-panel-soft)) !important;
    border-color:var(--side-border) !important;
    box-shadow:0 12px 28px rgba(0,0,0,.10) !important;
}
.stApp:has(.sidebar-theme-marker) .hud-world,
.stApp:has(.sidebar-theme-marker) .hud-stat,
.stApp:has(.sidebar-theme-marker) .hud-resource,
.stApp:has(.sidebar-theme-marker) .hud-mini-stat{
    background:var(--side-panel-soft) !important;
    border-color:var(--side-border) !important;
}
.stApp:has(.sidebar-theme-marker) .hud-bar-fill{
    background:linear-gradient(90deg,var(--side-accent),var(--side-accent-2)) !important;
}

/* Sidebar captions */
.stApp:has(.sidebar-theme-marker) section[data-testid="stSidebar"] .stCaption,
.stApp:has(.sidebar-theme-marker) section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
.stApp:has(.sidebar-theme-marker) section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p{
    color:var(--side-muted) !important;
}

/* Buttons: 특히 cute 테마에서 흰 박스/흰 글씨가 되지 않게 내부 p/span까지 명시 */
.stApp:has(.sidebar-theme-marker) section[data-testid="stSidebar"] .stButton>button{
    background:var(--side-panel) !important;
    border:1px solid var(--side-border) !important;
    color:var(--side-text) !important;
}
.stApp:has(.sidebar-theme-marker) section[data-testid="stSidebar"] .stButton>button p,
.stApp:has(.sidebar-theme-marker) section[data-testid="stSidebar"] .stButton>button span{
    color:var(--side-text) !important;
    -webkit-text-fill-color:var(--side-text) !important;
    opacity:1 !important;
}
.stApp:has(.sidebar-theme-marker) section[data-testid="stSidebar"] .stButton>button:hover{
    border-color:var(--side-accent) !important;
    box-shadow:0 0 0 1px var(--side-accent) inset !important;
}

/* Selectbox */
.stApp:has(.sidebar-theme-marker) section[data-testid="stSidebar"] [data-testid="stSelectbox"] label,
.stApp:has(.sidebar-theme-marker) section[data-testid="stSidebar"] [data-testid="stSelectbox"] label p{
    color:var(--side-text) !important;
}
.stApp:has(.sidebar-theme-marker) section[data-testid="stSidebar"] div[data-baseweb="select"],
.stApp:has(.sidebar-theme-marker) section[data-testid="stSidebar"] div[data-baseweb="select"]>div{
    background:var(--side-panel) !important;
    border-color:var(--side-border) !important;
    color:var(--side-text) !important;
}
.stApp:has(.sidebar-theme-marker) section[data-testid="stSidebar"] div[data-baseweb="select"] span,
.stApp:has(.sidebar-theme-marker) section[data-testid="stSidebar"] div[data-baseweb="select"] div{
    color:var(--side-text) !important;
    -webkit-text-fill-color:var(--side-text) !important;
}

/* Save alert */
.stApp:has(.sidebar-theme-marker) section[data-testid="stSidebar"] [data-testid="stAlert"]{
    background:var(--side-panel-soft) !important;
    border:1px solid var(--side-border) !important;
}
.stApp:has(.sidebar-theme-marker) section[data-testid="stSidebar"] [data-testid="stAlert"] p,
.stApp:has(.sidebar-theme-marker) section[data-testid="stSidebar"] [data-testid="stAlert"] div{
    color:var(--side-text) !important;
}

/* cute는 밝은 sidebar이므로 토글/아이콘도 어둡게 */
.stApp:has(.sidebar-theme-cute) section[data-testid="stSidebar"] button svg{
    color:#34475e !important;
    fill:#34475e !important;
}

/* large desktop width ------------------------------------------------------- */
@media (min-width:1200px){
    .stApp:has(.sidebar-theme-marker) [data-testid="stMainBlockContainer"]{
        width:min(96vw,1520px) !important;
    }
}
@media (max-width:900px){
    .stApp:has(.sidebar-theme-marker) [data-testid="stMainBlockContainer"]{
        padding-top:3.55rem !important;
        padding-left:.8rem !important;
        padding-right:.8rem !important;
    }
}

</style>
""", unsafe_allow_html=True)
