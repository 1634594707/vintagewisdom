export type SubDomain = {
  code: string;
  name: string;
};

export type Domain = {
  code: string;
  name: string;
  nameEn: string;
  icon: string;
  subDomains: SubDomain[];
};

export type QuickTag = {
  code: string;
  name: string;
  color: string;
};

export const DOMAINS: Domain[] = [
  {
    code: "TEC",
    name: "技术与产品",
    nameEn: "Technology",
    icon: "T",
    subDomains: [
      { code: "TEC-REF", name: "重构与迁移" },
      { code: "TEC-PLT", name: "平台演进" },
      { code: "TEC-OPS", name: "稳定性与运维" },
      { code: "TEC-AI", name: "AI 系统设计" },
    ],
  },
  {
    code: "CAR",
    name: "职业与选择",
    nameEn: "Career",
    icon: "C",
    subDomains: [
      { code: "CAR-NEG", name: "谈判与 offer 比较" },
      { code: "CAR-JOB", name: "岗位变动" },
      { code: "CAR-LEAD", name: "管理与影响力" },
      { code: "CAR-GRW", name: "成长路径" },
    ],
  },
  {
    code: "FIN",
    name: "金融与投资",
    nameEn: "Finance",
    icon: "F",
    subDomains: [
      { code: "FIN-INV", name: "投资决策" },
      { code: "FIN-RSK", name: "风险控制" },
      { code: "FIN-ALC", name: "资产配置" },
      { code: "FIN-MKT", name: "市场判断" },
    ],
  },
  {
    code: "HIS",
    name: "历史与治理",
    nameEn: "History",
    icon: "H",
    subDomains: [
      { code: "HIS-POL", name: "政治与改革" },
      { code: "HIS-WAR", name: "战争与冲突" },
      { code: "HIS-ORG", name: "组织演化" },
      { code: "HIS-CUL", name: "文化与社会变迁" },
    ],
  },
  {
    code: "LIF",
    name: "生活与关系",
    nameEn: "Life",
    icon: "L",
    subDomains: [
      { code: "LIF-HLT", name: "健康与习惯" },
      { code: "LIF-REL", name: "关系与协作" },
      { code: "LIF-DEC", name: "个人选择" },
      { code: "LIF-EMO", name: "情绪与压力" },
    ],
  },
];

export const QUICK_TAGS: QuickTag[] = [
  { code: "high-risk", name: "高风险", color: "#ef4444" },
  { code: "time-sensitive", name: "时效性强", color: "#f59e0b" },
  { code: "long-term", name: "长期决策", color: "#22c55e" },
  { code: "stakeholder", name: "多方博弈", color: "#3b82f6" },
  { code: "reversible", name: "可逆选择", color: "#6366f1" },
  { code: "irreversible", name: "不可逆选择", color: "#8b5cf6" },
];

const AUTO_CLASSIFY_RULES: Array<{
  domain: string;
  keywords: string[];
}> = [
  {
    domain: "TEC-REF",
    keywords: ["refactor", "rewrite", "migration", "technical debt", "重构", "迁移", "技术债"],
  },
  {
    domain: "TEC-AI",
    keywords: ["model", "llm", "agent", "embedding", "ai", "模型", "智能体"],
  },
  {
    domain: "CAR-NEG",
    keywords: ["offer", "salary", "promotion", "career", "job", "offer", "薪资", "跳槽", "晋升"],
  },
  {
    domain: "FIN-INV",
    keywords: ["investment", "portfolio", "valuation", "asset", "投资", "组合", "估值"],
  },
  {
    domain: "HIS-POL",
    keywords: ["reform", "institution", "coalition", "empire", "革命", "改革", "制度", "联盟"],
  },
  {
    domain: "LIF-REL",
    keywords: ["relationship", "family", "partner", "conflict", "关系", "家庭", "伴侣"],
  },
];

export function getMainDomain(code: string): Domain | undefined {
  const prefix = code.split("-")[0];
  return DOMAINS.find((domain) => domain.code === prefix);
}

export function autoClassifyDomain(text: string): Array<{ domain: string; confidence: number }> {
  const normalized = text.toLowerCase();

  return AUTO_CLASSIFY_RULES.map((rule) => {
    const hits = rule.keywords.filter((keyword) => normalized.includes(keyword.toLowerCase())).length;
    const confidence = Math.min(0.25 + hits * 0.18, 0.96);
    return {
      domain: rule.domain,
      confidence: hits > 0 ? confidence : 0,
    };
  })
    .filter((item) => item.confidence > 0)
    .sort((a, b) => b.confidence - a.confidence)
    .slice(0, 3);
}
