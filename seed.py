"""初始化测试数据"""

from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash
import app.models  # noqa: F401

from app.models.department import Department
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message

Base.metadata.create_all(bind=engine)

db = SessionLocal()

# ── 部门（6 条） ───────────────────────────────────────────────────────────────
dept_root   = Department(name="集团总部",      description="公司最高管理机构", sort_order=0)
dept_tech   = Department(name="技术部",        description="负责产品研发与运维", sort_order=1)
dept_ops    = Department(name="运营部",        description="负责日常运营管理", sort_order=2)
dept_sales  = Department(name="销售部",        description="负责市场销售业务", sort_order=3)
dept_fe     = Department(name="前端组",        description="前端开发小组", sort_order=0)
dept_be     = Department(name="后端组",        description="后端开发小组", sort_order=1)

db.add_all([dept_root, dept_tech, dept_ops, dept_sales])
db.flush()

dept_fe.parent_id = dept_tech.id
dept_be.parent_id = dept_tech.id
db.add_all([dept_fe, dept_be])
db.flush()

# ── 用户（8 条） ───────────────────────────────────────────────────────────────
pwd = get_password_hash("123456")

u_admin  = User(username="admin",    password=pwd, name="系统管理员", role="admin",
                email="admin@example.com",   department_id=dept_root.id)
u_tech   = User(username="zhangwei", password=pwd, name="张伟",       role="manager",
                email="zhangwei@example.com", phone="13800000001", department_id=dept_tech.id)
u_fe1    = User(username="liuyang",  password=pwd, name="刘洋",       role="user",
                email="liuyang@example.com",  phone="13800000002", department_id=dept_fe.id)
u_fe2    = User(username="wangling", password=pwd, name="王玲",       role="user",
                email="wangling@example.com", phone="13800000003", department_id=dept_fe.id)
u_be1    = User(username="chengang", password=pwd, name="陈刚",       role="user",
                email="chengang@example.com", phone="13800000004", department_id=dept_be.id)
u_be2    = User(username="zhaofang", password=pwd, name="赵芳",       role="user",
                email="zhaofang@example.com", phone="13800000005", department_id=dept_be.id)
u_ops    = User(username="sunna",    password=pwd, name="孙娜",       role="manager",
                email="sunna@example.com",    phone="13800000006", department_id=dept_ops.id)
u_sales  = User(username="lihao",    password=pwd, name="李浩",       role="user",
                email="lihao@example.com",    phone="13800000007", department_id=dept_sales.id)

db.add_all([u_admin, u_tech, u_fe1, u_fe2, u_be1, u_be2, u_ops, u_sales])
db.flush()

# ── 会话（6 条） ───────────────────────────────────────────────────────────────
conv1 = Conversation(title="如何学习 React?",       user_id=u_fe1.id)
conv2 = Conversation(title="前端性能优化方案",       user_id=u_fe1.id)
conv3 = Conversation(title="FastAPI 异步编程",       user_id=u_be1.id)
conv4 = Conversation(title="MySQL 索引优化",         user_id=u_be2.id)
conv5 = Conversation(title="团队 KPI 考核问题",      user_id=u_ops.id)
conv6 = Conversation(title="Q3 销售目标拆解",        user_id=u_sales.id)

db.add_all([conv1, conv2, conv3, conv4, conv5, conv6])
db.flush()

# ── 消息（26 条） ─────────────────────────────────────────────────────────────
messages = [
    # conv1 — React 学习
    Message(conversation_id=conv1.id, type="user",
            content="你好，请帮我解释一下 React Hooks 的工作原理？"),
    Message(conversation_id=conv1.id, type="assistant",
            content="React Hooks 是在函数式组件中使用状态和其他 React 特性的方式。\n\n**主要 Hooks 包括：**\n\n1. **useState** — 在函数组件中添加状态\n2. **useEffect** — 处理副作用（数据获取、订阅等）\n3. **useContext** — 访问 React Context\n4. **useReducer** — 复杂状态管理\n5. **useRef** — 访问 DOM 节点或保存可变值\n\nHooks 通过闭包和调用顺序跟踪组件状态，每次渲染时按相同顺序调用。"),
    Message(conversation_id=conv1.id, type="user",
            content="useEffect 的依赖数组有什么作用？"),
    Message(conversation_id=conv1.id, type="assistant",
            content="依赖数组控制 useEffect 何时运行：\n\n- **空数组 `[]`** — 仅在挂载时运行一次\n- **不传依赖数组** — 每次渲染后都运行\n- **包含依赖项** — 当依赖项变化时运行\n\n```javascript\nuseEffect(() => {\n  fetchData(userId)\n}, [userId])\n```\n\n不正确设置依赖数组会导致性能问题或死循环。"),
    Message(conversation_id=conv1.id, type="user",
            content="有没有推荐的学习资源？"),
    Message(conversation_id=conv1.id, type="assistant",
            content="推荐以下资源：\n\n1. **官方文档** — react.dev（新版，含交互式练习）\n2. **书籍** — 《React 设计原理》\n3. **视频** — B 站各大 UP 主的 React 实战课程\n4. **练习** — 在 CodeSandbox 上动手实现小 Demo\n\n建议从官方文档开始，边读边练效果最好。"),

    # conv2 — 前端性能
    Message(conversation_id=conv2.id, type="user",
            content="我们的页面首屏加载很慢，有什么优化方案？"),
    Message(conversation_id=conv2.id, type="assistant",
            content="首屏性能优化主要从以下几个维度入手：\n\n**资源层面**\n- 代码分割（Code Splitting）+ 懒加载\n- 图片压缩 & WebP 格式\n- CDN 加速静态资源\n\n**网络层面**\n- HTTP/2 多路复用\n- 开启 Gzip/Brotli 压缩\n- 预加载（`<link rel=preload>`）\n\n**渲染层面**\n- 服务端渲染（SSR）或静态生成（SSG）\n- 骨架屏减少视觉等待\n\n先用 Lighthouse 跑一下诊断报告，找到瓶颈再针对性优化。"),
    Message(conversation_id=conv2.id, type="user",
            content="代码分割具体怎么做？"),
    Message(conversation_id=conv2.id, type="assistant",
            content="在 React + Vite 项目中代码分割很简单：\n\n```javascript\n// 路由级别懒加载\nconst Dashboard = lazy(() => import('./pages/Dashboard'))\n\nfunction App() {\n  return (\n    <Suspense fallback={<Spinner />}>\n      <Routes>\n        <Route path=\"/dashboard\" element={<Dashboard />} />\n      </Routes>\n    </Suspense>\n  )\n}\n```\n\nVite 会自动将每个动态 import 打包为独立 chunk，首屏只加载必要的代码。"),

    # conv3 — FastAPI 异步
    Message(conversation_id=conv3.id, type="user",
            content="FastAPI 中异步路由和同步路由有什么区别？"),
    Message(conversation_id=conv3.id, type="assistant",
            content="核心区别在于线程模型：\n\n- **`async def` 路由** — 在事件循环中运行，适合 I/O 密集型操作（调用异步数据库、HTTP 请求）\n- **`def` 路由** — FastAPI 自动将其放入线程池运行，不阻塞事件循环\n\n```python\n# 异步路由：使用 await\n@app.get('/users')\nasync def get_users(db: AsyncSession = Depends(get_db)):\n    result = await db.execute(select(User))\n    return result.scalars().all()\n```\n\n如果路由内有同步阻塞操作（如普通 requests 调用），应改用 `def` 或将阻塞操作放入 `run_in_executor`。"),
    Message(conversation_id=conv3.id, type="user",
            content="SQLAlchemy 异步会话怎么配置？"),
    Message(conversation_id=conv3.id, type="assistant",
            content="需要使用 `sqlalchemy.ext.asyncio`：\n\n```python\nfrom sqlalchemy.ext.asyncio import create_async_engine, AsyncSession\nfrom sqlalchemy.orm import sessionmaker\n\nengine = create_async_engine(\n    'mysql+aiomysql://user:pwd@host/db',\n    echo=False,\n)\n\nAsyncSessionLocal = sessionmaker(\n    engine, class_=AsyncSession, expire_on_commit=False\n)\n\nasync def get_db():\n    async with AsyncSessionLocal() as session:\n        yield session\n```\n\n驱动需换成 `aiomysql`（MySQL）或 `asyncpg`（PostgreSQL）。"),

    # conv4 — MySQL 索引
    Message(conversation_id=conv4.id, type="user",
            content="我们有一张 500 万行的订单表，查询很慢，如何优化？"),
    Message(conversation_id=conv4.id, type="assistant",
            content="先用 `EXPLAIN` 分析慢查询，常见优化思路：\n\n1. **加索引** — 在 WHERE、ORDER BY、JOIN 字段上建索引\n2. **联合索引** — 遵循最左前缀原则，把区分度高的字段放前面\n3. **避免全表扫描** — 不要在索引列上做函数运算\n4. **分页优化** — 大偏移量用 `WHERE id > last_id LIMIT 20` 替代 `LIMIT 100000,20`\n5. **读写分离** — 查询走从库\n\n先把慢 SQL 贴出来，我帮你具体分析。"),
    Message(conversation_id=conv4.id, type="user",
            content="联合索引的顺序怎么确定？"),
    Message(conversation_id=conv4.id, type="assistant",
            content="联合索引字段顺序原则：\n\n1. **区分度高的字段放前面** — 如 `status` 只有几个值，`user_id` 有百万级，`user_id` 应在前\n2. **等值查询字段在范围查询字段前** — `WHERE a=1 AND b>10` → 索引建 `(a, b)`\n3. **覆盖索引** — 把 SELECT 的字段也加入索引，避免回表\n\n```sql\n-- 查询：WHERE user_id=? AND status=? ORDER BY created_at\nCREATE INDEX idx_order ON orders(user_id, status, created_at);\n```"),

    # conv5 — 运营 KPI
    Message(conversation_id=conv5.id, type="user",
            content="团队 KPI 考核指标如何设计比较合理？"),
    Message(conversation_id=conv5.id, type="assistant",
            content="KPI 设计建议遵循 SMART 原则：\n\n- **Specific** — 指标具体，如「月活用户数」而非「用户增长」\n- **Measurable** — 可量化，有明确数据来源\n- **Achievable** — 跳一跳能够到，不能过高或过低\n- **Relevant** — 与团队目标强相关\n- **Time-bound** — 有明确考核周期\n\n运营团队常见指标：DAU/MAU、用户留存率、转化率、内容发布量、投诉解决时效等。建议结果指标与过程指标各占 50%。"),
    Message(conversation_id=conv5.id, type="user",
            content="怎么避免考核指标导致数据造假？"),
    Message(conversation_id=conv5.id, type="assistant",
            content="防止数据注水的几个机制：\n\n1. **交叉验证** — 多个数据源对比，如 DAU 和服务器日志要对得上\n2. **过程可追溯** — 保留操作日志，异常波动可查原因\n3. **设置负向指标** — 如「用户投诉率」，只刷正向指标会被负向指标拖累\n4. **定期抽查** — 随机抽取样本人工核实\n5. **文化建设** — 让团队理解 KPI 是工具而非目的，治本之道\n\n制度设计上避免单一指标一票否决，组合评估更健康。"),

    # conv6 — 销售目标
    Message(conversation_id=conv6.id, type="user",
            content="Q3 销售目标 500 万，怎么合理拆解到每个人？"),
    Message(conversation_id=conv6.id, type="assistant",
            content="目标拆解建议按以下步骤：\n\n1. **历史基线** — 看各人 Q2 完成情况和客户资源\n2. **能力分层** — 老员工目标可稍高，新人有爬坡期（如前两月 60%，第三月 100%）\n3. **区域/行业分配** — 按各人负责的市场潜力加权\n4. **预留缓冲** — 个人目标总和设为 550 万，留 10% 缓冲\n5. **里程碑检查** — 每月末 review 进度，及时调整资源支持\n\n建议用 Excel 做一张拆解表，把逻辑和数字都透明给团队。"),
    Message(conversation_id=conv6.id, type="user",
            content="如果到 7 月底完成率只有 30%，怎么挽救？"),
    Message(conversation_id=conv6.id, type="assistant",
            content="完成率偏低时的挽救策略：\n\n**短期动作（本月）**\n- 重点跟进进入决策阶段的商机，优先保成单\n- 临时调整提成比例激励冲刺\n\n**中期调整（Q3 剩余两月）**\n- 聚焦大客户，放弃低价值长尾\n- 引入市场支持，加大品牌曝光\n- 向上汇报，争取价格或资源上的特批\n\n**目标层面**\n- 如外部环境有重大变化（如行业政策），可以和管理层协商合理调整目标，不要死扛\n\n最重要的是快速找到卡点：是线索不够、转化率低还是客单价低，对症下药。"),
]

db.add_all(messages)
db.commit()

# ── 汇总 ──────────────────────────────────────────────────────────────────────
print(f"部门: {db.query(Department).count()} 条")
print(f"用户: {db.query(User).count()} 条")
print(f"会话: {db.query(Conversation).count()} 条")
print(f"消息: {db.query(Message).count()} 条")
print("测试数据初始化完成！")

db.close()
