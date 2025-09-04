#!/bin/bash
# Cloud SQL 成本管理腳本

case "$1" in
  start)
    echo "🚀 啟動 Cloud SQL..."
    gcloud sql instances patch duotopia-staging-0827 --activation-policy=ALWAYS
    echo "✅ Cloud SQL 已啟動（每天 $2.28）"
    echo "⚠️  記得用完要停止！使用: ./scripts/manage-db.sh stop"
    ;;

  stop)
    echo "🛑 停止 Cloud SQL..."
    gcloud sql instances patch duotopia-staging-0827 --activation-policy=NEVER
    echo "✅ Cloud SQL 已停止（不再收費）"
    ;;

  status)
    echo "📊 檢查 Cloud SQL 狀態..."
    gcloud sql instances describe duotopia-staging-0827 --format="value(state,settings.activationPolicy)"
    ;;

  cost)
    echo "💰 成本預估："
    STATUS=$(gcloud sql instances describe duotopia-staging-0827 --format="value(settings.activationPolicy)")
    if [ "$STATUS" = "ALWAYS" ]; then
      echo "狀態: 運行中 ⚡"
      echo "每日成本: $2.28 USD"
      echo "每月成本: $68.40 USD"
      echo "💡 提示: 不用時請執行 ./scripts/manage-db.sh stop"
    else
      echo "狀態: 已停止 💤"
      echo "每日成本: $0 USD"
      echo "💡 提示: 需要時執行 ./scripts/manage-db.sh start"
    fi
    ;;

  *)
    echo "使用方法："
    echo "  ./scripts/manage-db.sh start  - 啟動資料庫"
    echo "  ./scripts/manage-db.sh stop   - 停止資料庫（省錢）"
    echo "  ./scripts/manage-db.sh status - 檢查狀態"
    echo "  ./scripts/manage-db.sh cost   - 查看成本"
    ;;
esac
