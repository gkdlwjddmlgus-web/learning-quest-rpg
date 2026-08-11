from game_core import *


def render_record_tab() -> None:
    st.subheader("📊 학습 기록")
    st.caption("문제를 제출한 기록을 기준으로 학습량과 정답률을 확인합니다. 새 버전 설치 이후의 제출부터 기록됩니다.")

    active_record_world = get_active_learning_world()
    scope_col, period_col = st.columns(2)

    scope_options = ["전체 월드"]
    record_worlds = get_learning_worlds()
    scope_options.extend([f"{world['world_name']} · {world['topic']}" for world in record_worlds])
    selected_scope = scope_col.selectbox("분석 범위", scope_options, key="record_scope")
    period = period_col.selectbox("기간", ["최근 7일", "최근 30일", "전체"], key="record_period")

    selected_world_id = None
    selected_world = None
    if selected_scope != "전체 월드":
        selected_world = next(
            (world for world in record_worlds if f"{world['world_name']} · {world['topic']}" == selected_scope),
            None,
        )
        if selected_world:
            selected_world_id = int(selected_world["id"])

    days = 7 if period == "최근 7일" else 30 if period == "최근 30일" else None
    attempts = get_question_attempts(
        current_user_id(),
        world_id=selected_world_id,
        days=days,
    )

    if not attempts:
        st.info("아직 이 범위에 저장된 학습 기록이 없습니다. 문제를 한 번 제출하면 여기부터 기록되기 시작합니다.")
    else:
        df = pd.DataFrame(attempts)

        # 현재 Supabase 스키마는 created_at을 사용한다.
        # 예전 SQLite/레거시 데이터에 attempted_at이 남아 있어도 호환한다.
        if "created_at" in df.columns:
            time_source = "created_at"
        elif "attempted_at" in df.columns:
            time_source = "attempted_at"
        else:
            st.error("학습 기록에서 시간 컬럼을 찾을 수 없습니다.")
            return

        df["attempted_at"] = pd.to_datetime(
            df[time_source],
            errors="coerce",
        )
        df = df.dropna(subset=["attempted_at"])

        if df.empty:
            st.info("선택한 범위에 유효한 시간 정보가 있는 학습 기록이 없습니다.")
            return

        df["is_correct_num"] = df["is_correct"].astype(int)
        df["date"] = df["attempted_at"].dt.date.astype(str)

        total_attempts = len(df)
        total_correct = int(df["is_correct_num"].sum())
        total_wrong = total_attempts - total_correct
        accuracy = (total_correct / total_attempts * 100) if total_attempts else 0.0
        today_count = int((df["attempted_at"].dt.date == date.today()).sum())

        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("총 풀이", f"{total_attempts}회")
        k2.metric("정답", f"{total_correct}회")
        k3.metric("오답", f"{total_wrong}회")
        k4.metric("정답률", f"{accuracy:.1f}%")
        k5.metric("오늘 풀이", f"{today_count}회")

        st.caption(f"🔥 현재 연속 학습 {st.session_state.extra.get('streak', 0)}일 · 현재 레벨 Lv.{st.session_state.level}")
        st.divider()

        recommendation_world = selected_world or active_record_world
        recommendation = build_weakness_recommendation(recommendation_world)
        with st.container(border=True):
            render_recommendation_card(recommendation)
            if recommendation_world and recommendation:
                if selected_world_id is not None and active_record_world and int(active_record_world["id"]) != int(recommendation_world["id"]):
                    st.caption("이 추천은 현재 활성 월드가 아닌 분석 대상으로 선택한 월드의 기록을 기준으로 합니다.")
                if st.button(
                    "📜 이 추천을 퀘스트 설정에 반영",
                    key=f"record_apply_rec_{recommendation_world['id']}",
                    width="stretch",
                ):
                    if not recommendation_world.get("is_active"):
                        set_active_learning_world(int(recommendation_world["id"]))
                    st.session_state.quest_world_id = int(recommendation_world["id"])
                    st.session_state.selected_category = recommendation["subject_name"]
                    st.session_state.selected_difficulty = recommendation["difficulty"]
                    reset_question()
                    st.success("추천 분야와 난이도를 퀘스트에 반영했습니다. 📜 퀘스트 탭에서 바로 시작할 수 있습니다.")

        st.divider()
        st.markdown("### 최근 학습량")
        if days is not None:
            start_day = date.today() - timedelta(days=days - 1)
            date_labels = [(start_day + timedelta(days=i)).isoformat() for i in range(days)]
            daily_counts = df.groupby("date").size().reindex(date_labels, fill_value=0)
        else:
            daily_counts = df.groupby("date").size().sort_index()

        daily_chart = pd.DataFrame({"풀이 수": daily_counts.values}, index=daily_counts.index)
        st.bar_chart(daily_chart, width="stretch")

        c_left, c_right = st.columns(2)

        with c_left:
            st.markdown("### 분야별 성과")
            subject_stats = (
                df.groupby("category")
                .agg(풀이수=("id", "count"), 정답수=("is_correct_num", "sum"))
                .reset_index()
            )
            subject_stats["정답률"] = (subject_stats["정답수"] / subject_stats["풀이수"] * 100).round(1)
            subject_stats = subject_stats.sort_values(["정답률", "풀이수"], ascending=[False, False])
            st.dataframe(
                subject_stats.rename(columns={"category": "분야"}),
                width="stretch",
                hide_index=True,
            )

        with c_right:
            st.markdown("### 난이도별 성과")
            difficulty_order = ["쉬움", "보통", "어려움"]
            diff_stats = (
                df.groupby("difficulty")
                .agg(풀이수=("id", "count"), 정답수=("is_correct_num", "sum"))
                .reset_index()
            )
            diff_stats["정답률"] = (diff_stats["정답수"] / diff_stats["풀이수"] * 100).round(1)
            diff_stats["_order"] = diff_stats["difficulty"].map({v: i for i, v in enumerate(difficulty_order)}).fillna(99)
            diff_stats = diff_stats.sort_values("_order").drop(columns="_order")
            st.dataframe(
                diff_stats.rename(columns={"difficulty": "난이도"}),
                width="stretch",
                hide_index=True,
            )

        st.markdown("### 취약 분야")
        eligible = subject_stats[subject_stats["풀이수"] >= 2].sort_values(["정답률", "풀이수"], ascending=[True, False])
        if eligible.empty:
            st.caption("분야별로 최소 2회 이상 풀면 취약 분야를 보여줍니다.")
        else:
            for rank, (_, row) in enumerate(eligible.head(3).iterrows(), start=1):
                st.write(f"{rank}. **{row['category']}** · 정답률 {row['정답률']:.1f}% · {int(row['풀이수'])}회 풀이")

        st.markdown("### 최근 제출 기록")
        recent = df.sort_values("attempted_at", ascending=False).head(15).copy()
        recent["결과"] = recent["is_correct_num"].map({1: "✅ 정답", 0: "❌ 오답"})
        recent["시간"] = recent["attempted_at"].dt.strftime("%m-%d %H:%M")
        recent["구분"] = recent["attempt_type"].map({"quest": "퀘스트", "review": "오답 복습"}).fillna(recent["attempt_type"])
        st.dataframe(
            recent[["시간", "category", "difficulty", "결과", "구분", "xp_earned"]].rename(
                columns={"category": "분야", "difficulty": "난이도", "xp_earned": "획득 XP"}
            ),
            width="stretch",
            hide_index=True,
        )

