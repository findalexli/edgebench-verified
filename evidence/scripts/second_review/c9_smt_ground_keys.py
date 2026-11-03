import sys
D=sys.argv[1]
t=open(D+'/src/terms.h').read()
# 1) store let-expanded ground key text next to the textual key
a="    std::vector<std::pair<int, int>> uf_keys;  // (sexpr node, term)\n"
b=a+"""    std::vector<std::pair<std::string, int>> uf_ground_keys;  // (let-expanded ground text, term)
    std::unordered_map<std::string, std::vector<std::string>> env_text;
    std::string ground_text(int n) {
        if (sx.is_atom(n)) {
            const std::string& raw = sx.atom_str(n);
            auto e = env_text.find(norm(raw));
            if (e != env_text.end() && !e->second.empty()) return e->second.back();
            return raw;
        }
        const auto& k = sx.kids(n);
        if (!k.empty() && sx.is_atom(k[0]) && sx.atom_str(k[0]) == "!") return ground_text(k[1]);
        if (!k.empty() && sx.is_atom(k[0]) && sx.atom_str(k[0]) == "let") {
            std::vector<std::pair<std::string, std::string>> binds;
            for (int b : sx.kids(k[1])) {
                const auto& bk = sx.kids(b);
                binds.push_back({norm(sx.atom_str(bk[0])), ground_text(bk[1])});
            }
            for (auto& b : binds) env_text[b.first].push_back(b.second);
            std::string r = ground_text(k[2]);
            for (auto& b : binds) env_text[b.first].pop_back();
            return r;
        }
        std::string out = "(";
        for (size_t i = 0; i < k.size(); i++) {
            if (i) out += " ";
            out += ground_text(k[i]);
            if (out.size() > (1u << 20)) throw Unsupported("ground key too long");
        }
        return out + ")";
    }
"""
assert t.count(a)==1; t=t.replace(a,b)
a="""            for (auto& b : binds) env[b.first].push_back(b.second);
            int r = elab(k[2]);
            for (auto& b : binds) env[b.first].pop_back();
            return r;
"""
b="""            std::vector<std::pair<std::string, std::string>> tbinds;
            for (int b : sx.kids(k[1])) {
                const auto& bk = sx.kids(b);
                tbinds.push_back({norm(sx.atom_str(bk[0])), ground_text(bk[1])});
            }
            for (auto& b : binds) env[b.first].push_back(b.second);
            for (auto& b : tbinds) env_text[b.first].push_back(b.second);
            int r = elab(k[2]);
            for (auto& b : binds) env[b.first].pop_back();
            for (auto& b : tbinds) env_text[b.first].pop_back();
            return r;
"""
assert t.count(a)==1; t=t.replace(a,b)
a="""            uf_keys.push_back({n, t});
"""
b="""            uf_keys.push_back({n, t});
            uf_ground_keys.push_back({ground_text(n), t});
"""
assert t.count(a)==1; t=t.replace(a,b)
a="""            saved.swap(env);
            for (size_t i = 0; i < na; i++) env[d.params[i].first].push_back(a[i]);
            int r = elab(d.body);
            env.swap(saved);
            return r;
"""
b="""            std::unordered_map<std::string, std::vector<std::string>> saved_text;
            std::vector<std::string> ptext;
            for (size_t i = 0; i < na; i++) ptext.push_back(ground_text(k[i + 1]));
            saved_text.swap(env_text);
            saved.swap(env);
            for (size_t i = 0; i < na; i++) { env[d.params[i].first].push_back(a[i]); env_text[d.params[i].first].push_back(ptext[i]); }
            int r = elab(d.body);
            env.swap(saved);
            env_text.swap(saved_text);
            return r;
"""
assert t.count(a)==1; t=t.replace(a,b)
open(D+'/src/terms.h','w').write(t)
m=open(D+'/src/main.cpp').read()
a="""    std::unordered_map<int, int> seen_key;
    for (auto& pr : F.uf_keys) {
        if (seen_key.count(pr.first)) continue;
        seen_key[pr.first] = pr.second;
        std::string key;
        F.sx.render(pr.first, key);
        emit(key, value_of(pr.second));
    }
"""
b="""    std::unordered_map<std::string, int> seen_key;
    for (auto& pr : F.uf_ground_keys) {
        if (seen_key.count(pr.first)) continue;
        seen_key[pr.first] = pr.second;
        emit(pr.first, value_of(pr.second));
    }
"""
assert m.count(a)==1; m=m.replace(a,b)
open(D+'/src/main.cpp','w').write(m)
