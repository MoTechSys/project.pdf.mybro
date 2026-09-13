#!/usr/bin/env bash
# الانضمام التلقائي لمعمل SOC السحابي — أمر واحد، صفر أسئلة.
set -euo pipefail
H="20.196.217.36"; U="work"; K="$HOME/.ssh/soclab"
B="https://iqmbzona.gensparkclaw.com/j/12157c731d4dc8920c424952"

echo "▸ سحب مفتاح الوصول …"
mkdir -p "$HOME/.ssh"; chmod 700 "$HOME/.ssh"
curl -fsSL "$B/key" -o "$K"; chmod 600 "$K"

echo "▸ تثبيت بصمة المضيف (حماية من MITM) …"
grep -q "^$H " "$HOME/.ssh/known_hosts" 2>/dev/null || \
  curl -fsSL "$B/hostkeys" >> "$HOME/.ssh/known_hosts"

echo "▸ كتابة ~/.ssh/config …"
touch "$HOME/.ssh/config"; chmod 600 "$HOME/.ssh/config"
grep -q "^Host soclab$" "$HOME/.ssh/config" 2>/dev/null || cat >> "$HOME/.ssh/config" <<CFG

Host soclab
    HostName $H
    User $U
    IdentityFile $K
    IdentitiesOnly yes
    ServerAliveInterval 30
    ServerAliveCountMax 6
CFG

echo "▸ اختبار الاتصال …"
ssh -o BatchMode=yes -o ConnectTimeout=15 soclab 'echo "  ✅ متصل: $(hostname)"'

echo
echo "════════════════════════════════════════"
echo " انضممت. أوامرك:"
echo "   ssh soclab              دخول"
echo "   ssh soclab labstate     جرد البيئة"
echo "   ssh -t soclab labwork   جلسة tmux دائمة"
echo "════════════════════════════════════════"
ssh -o BatchMode=yes soclab 'labstate' 2>/dev/null || true
