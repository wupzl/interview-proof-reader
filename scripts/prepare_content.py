"""Preserve the manuscript and derive seven independently editable chapters."""
from pathlib import Path
import hashlib, json, re, shutil

ROOT = Path(__file__).resolve().parents[1]
TITLES = ['你知道，不代表他知道', '追问陷阱', '简历里的数字', '黄金九十秒', '反问的艺术', '被记住的人', '压力面试']
TOPICS = ['把知识、贡献与证据讲清楚', '面对连续追问，解释机制与边界', '让每一个指标都有测量口径', '用九十秒建立有效的技术对话', '用最后五分钟了解团队与岗位', '用真实证据形成清晰的技术画像', '面对质疑，保持判断与表达']
NOTES = [
    '表达不能替代实践。模板中的个人贡献、测试和上线经历，需要逐项核对后再使用。',
    '线程池示例假定普通有界队列、线程均繁忙且任务未提前完成；实际线程数取决于提交与执行时序。',
    '本章数字均为虚构教学示例。Little 定律适用于稳定系统的长期平均量，不能把任意峰值直接代入。',
    '三十秒、九十秒与三分钟是训练约束，不是统一面试标准。先回应问题，再按对方兴趣展开。',
    '反问用于了解岗位与团队；效果取决于情境，不保证改变录用判断。',
    '技术画像与自评用于整理证据，不代表公司标准，也不构成对读者真实能力的判断。',
    '先区分事实错误、信息不足与观点分歧。承认确实存在的问题，同时保留对不合理评价的判断。',
]

def main():
    (ROOT/'source').mkdir(parents=True, exist_ok=True)
    (ROOT/'chapters').mkdir(exist_ok=True)
    original = ROOT/'source'/'interviewdescription.md'
    if not original.exists():
        shutil.copyfile(ROOT.parent/'interviewdescription.md', original)
    source = original.read_text(encoding='utf-8').replace('\r\n', '\n')
    # The chapter-seven teaser also has an H1. A real chapter begins with its epigraph.
    pattern = r'^# 《面试官的审判》第([一二三四五六七])章：([^\n]+)\n\s*\n(?=——)'
    starts = list(re.finditer(pattern, source, re.M))
    assert len(starts) == 7, 'Expected seven real chapter openings'
    chapters = []
    for i, match in enumerate(starts):
        text = source[match.end():starts[i+1].start() if i<6 else len(source)].strip()
        text = re.sub(r'\n下一章。\s*$', '', text)
        # These fragments are flattened widget controls, not lost prose.
        if i == 0:
            text = re.sub(r'^模拟面试\n.*?(?=下一章预告：)', '本章训练：介绍一个真实项目，分别写出业务目标、个人贡献、关键决策和验证证据。完成后，对照章末训练清单复盘。\n\n', text, flags=re.S|re.M)
        if i == 1:
            text = text.replace('你近期面试中暴露的两个真实问题', '故事中出现的两类问题')
        if i == 2:
            text = re.sub(r'同一次压测的其他指标\n.*?(?=虚构的教学示例)', '同一次压测的其他指标\n\n| 指标 | 示例值 |\n| --- | --- |\n| 吞吐量 | 5,000 req/s |\n| P99 延迟 | 8.6 秒 |\n| 失败率 | 17% |\n| CPU 利用率 | 99% |\n\n', text, flags=re.S)
        if i == 3:
            text = text.replace('30 秒90 秒3 分钟', '**三个表达版本：30 秒、90 秒、3 分钟。**\n\n下面是一份 90 秒版本的演练示例。')
            text = text.replace('&#x20;复制版本', '').replace('\\\n', '\n')
            text = text.replace('这是以已讨论的项目方向编写的演练稿，不代表其中每个模块都已经在你的项目中完成；正式使用前需要核对真实贡献。', '这是一份虚构项目的演练稿。读者使用前，应按真实经历逐项核对模块实现与个人贡献。')
            text = text.replace('对于你目前准备的 AI Agent、RAG 和 Java 后端相关岗位，我建议重点训练三种能力。', '围绕林远准备的 AI Agent、RAG 和 Java 后端岗位，可以重点训练三种能力。')
            text = text.replace('尤其是你之前面试中出现过的两个反馈——工程落地经验不足、项目数据说服力不强——不能仅靠优化九十秒话术解决。', '故事中反复出现的两类反馈——工程落地经验不足、项目数据说服力不强——不能仅靠优化九十秒话术解决。')
            text = re.sub(r'将真实经历填进去，生成一份可以用于技术面试的项目论证提纲。\n.*?(?=### 下一章预告)', '将真实经历写成六项：项目目标、个人负责的模块、遇到的问题、备选方案与取舍、验证证据、尚未完成的边界。章末训练提供可填写的证据卡。\n\n', text, flags=re.S)
        if i == 4:
            text = re.sub(r'3 / 3 已选\n.*?(?=周衡说：)', '面试前，按岗位选择一到三个问题，每个问题再准备一个合理追问：\n\n| 方向 | 可以提出的问题 | 想了解什么 |\n| --- | --- | --- |\n| Agent 可靠性 | 当前最难的工程挑战是工具调用、状态管理还是结果验证？ | 团队实际面对的问题 |\n| Agent 评测 | 如何将真实失败案例转成回归任务？ | 质量反馈是否形成闭环 |\n| Java 后端 | 新人有机会参与哪些性能优化与故障排查？ | 工程实践机会 |\n| 产品工程 | 工程师如何参与产品决策和上线后的效果迭代？ | 岗位职责边界 |\n| 成长路径 | 前三到六个月通常承担什么任务，怎样判断能够独立负责模块？ | 培养方式与工作预期 |\n| 针对反馈 | 团队希望应届生提前积累哪些工程实践？ | 有针对性的准备方向 |\n\n', text, flags=re.S)
        if i == 5:
            text = re.sub(r'按照实际情况评分。.*?(?=### 下一章预告)', '从四个方向整理自己的证据：RAG 检索与评测、Coding Agent 工程、Java 服务端工程、Java 基础与系统原理。\n\n每个方向分别检查：能否解释原理、是否有亲自实现的案例、是否有可核实的验证材料。未做过的部分如实留空，避免用预填分数替代真实判断。\n\n选择证据最充分的一个方向，整理至少两个具体案例、一个技术取舍和一份验证材料。章末训练提供自评清单与补充计划。\n\n', text, flags=re.S)
            text = text.replace('# 《面试官的审判》第七章：', '**第七章预告：').replace('时，你应该怎么办？\n\n林远将遇到', '时，你应该怎么办？**\n\n林远将遇到')
        if i == 6:
            text = re.sub(r'压力面试模拟\n.*?(?=### 下一章预告)', '本章训练将围绕四类质疑展开：项目是否只是调用 API、框架之外的理解、性能数据的依据，以及个人贡献的边界。先承认合理的限制，再给出具体证据，最后说明验证办法。\n\n', text, flags=re.S)
        # Accessible Unicode replaces the handful of malformed exported TeX fragments.
        formulas = [
            (r'\text{面试中的能力呈现} \approx \text{真实能力}\times\text{表达有效性}', '面试中的能力呈现 ≈ 真实能力 × 表达有效性'),
            (r'L=\lambda W', 'L = λ × W'),
            (r'L=10000\times0.1=1000', 'L = 10,000 × 0.1 = 1,000'),
            (r'L=100\times30=3000', 'L = 100 × 30 = 3,000'),
            (r'\frac{420-310}{420}\times100\\% \approx26.2\\%', '(420 − 310) ÷ 420 × 100% ≈ 26.2%'),
            (r'Recall\@10(q)= \frac{|G_q\cap R_q^{10}|}{|G_q|}', 'Recall@10(q) = |G_q ∩ R_q¹⁰| ÷ |G_q|'),
            (r'\text{方案价值} =f(\text{质量},\text{延迟},\text{成本},\text{可靠性})', '方案价值 = f(质量，延迟，成本，可靠性)'),
            (r'\text{有效回答}= \text{结论}+\text{理由}+\text{可追问点}', '有效回答 = 结论 + 理由 + 可追问点'),
            (r'\text{有效回应} = \text{识别命题} + \text{承认边界} + \text{提供证据}', '有效回应 = 识别命题 + 承认边界 + 提供证据'),
        ]
        for tex, readable in formulas:
            text = text.replace(r'\\[ '+tex+r' \\]', '> '+readable)
        text = text.replace(r'\\(G_q\\)', '`G_q`').replace(r'\\(R_q^{10}\\)', '`R_q¹⁰`')
        text = text.replace(r'\@', '@').replace('&#x20;', '')
        text = re.sub(r'\n{3,}', '\n\n', text).strip()
        assert '\\[' not in text, f'Unconverted formula in chapter {i+1}'
        heading = f'# 第{i+1}章 · {TITLES[i]}'
        (ROOT/'chapters'/f'{i+1:02}.md').write_text(heading+'\n\n'+text+'\n', encoding='utf-8')
        chapters.append({'number':i+1,'title':TITLES[i],'subtitle':match[2], 'topics':TOPICS[i], 'note':NOTES[i]})
    book = {'title':'面试官的审判','slug':'interview-proof-reader','status':'连载','nextChapter':8,'chapters':chapters}
    (ROOT/'book.json').write_text(json.dumps(book,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    audit = {'source':'source/interviewdescription.md','sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'chapters':7,'nextChapter':'第八章仅有预告，未续写','approach':'保留人物与情节；清理导出控件；公开阅读措辞；独立技术说明；七组本地训练'}
    (ROOT/'CONTENT_REVIEW.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Prepared seven chapters; original manuscript preserved byte for byte.')

if __name__ == '__main__': main()
