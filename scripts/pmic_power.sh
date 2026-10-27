#!/bin/bash
vcgencmd pmic_read_adc | awk '
/current/ { n=$1; sub(/_A$/,"",n); i=$2; sub(/.*=/,"",i); sub(/A$/,"",i); cur[n]=i }
/volt/ { n=$1; sub(/_V$/,"",n); v=$2; sub(/.*=/,"",v); sub(/V$/,"",v); vol[n]=v }
END { for (k in cur) if (k in vol) s+=cur[k]*vol[k]; printf "%.2f\n", s }'
