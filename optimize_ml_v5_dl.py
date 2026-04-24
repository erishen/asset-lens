"""
ML准确率优化脚本 v5 - 深度学习
目标: 72% → 80%

策略:
1. LSTM模型捕捉时序特征
2. Attention机制
3. 多尺度特征
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from asset_lens.db.database import db_manager
from asset_lens.ml.features import FeatureEngineer

try:
    import torch
    from torch import nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    nn = None


class LSTMModel(nn.Module):
    """LSTM模型"""
    
    def __init__(self, input_dim, hidden_dim=128, num_layers=2, dropout=0.3):
        super().__init__()
        
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=True,
        )
        
        self.attention = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
            nn.Softmax(dim=1),
        )
        
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim * 2, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1),
            nn.Sigmoid(),
        )
    
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        
        attn_weights = self.attention(lstm_out)
        context = torch.sum(attn_weights * lstm_out, dim=1)
        
        out = self.fc(context)
        return out.squeeze(-1)


class TransformerModel(nn.Module):
    """Transformer模型"""
    
    def __init__(self, input_dim, d_model=64, nhead=4, num_layers=2, dropout=0.3):
        super().__init__()
        
        self.input_proj = nn.Linear(input_dim, d_model)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            batch_first=True,
        )
        
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        self.fc = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1),
            nn.Sigmoid(),
        )
    
    def forward(self, x):
        x = self.input_proj(x)
        x = self.transformer(x)
        x = x.mean(dim=1)
        out = self.fc(x)
        return out.squeeze(-1)


def create_sequences(X, y, seq_length=20):
    """创建时序序列"""
    X_seq = []
    y_seq = []
    
    for i in range(seq_length, len(X)):
        X_seq.append(X[i-seq_length:i])
        y_seq.append(y[i])
    
    return np.array(X_seq), np.array(y_seq)


def prepare_data(days: int = 500, seq_length: int = 20):
    """准备训练数据"""
    print(f"📥 获取训练数据 ({days} 天)...")
    
    klines_data = db_manager.get_klines_for_ml(days=days)
    
    stocks_data = {}
    for code, klines in klines_data.items():
        if len(klines) < 60:
            continue
        
        df = pd.DataFrame(klines)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        for col in ['open', 'close', 'high', 'low', 'volume', 'amount']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        stocks_data[code] = df
    
    print(f"📊 成功加载 {len(stocks_data)} 只股票的数据")
    
    feature_engineer = FeatureEngineer()
    all_X = []
    all_y = []
    
    for code, df in stocks_data.items():
        df_features = feature_engineer.calculate_all_features(df)
        
        future_return = df_features['close'].shift(-5) / df_features['close'] - 1
        
        def label_return(r):
            if pd.isna(r):
                return -1
            if r >= 0.02:
                return 1
            elif r <= -0.02:
                return 0
            else:
                return -1
        
        y = future_return.apply(label_return)
        
        valid_mask = y != -1
        X = df_features[valid_mask].copy()
        y_valid = y[valid_mask].copy()
        
        feature_cols = feature_engineer.feature_names
        X = X[feature_cols].fillna(0).replace([np.inf, -np.inf], 0)
        
        all_X.append(X)
        all_y.append(y_valid)
    
    X_all = pd.concat(all_X, ignore_index=True)
    y_all = pd.concat(all_y, ignore_index=True)
    
    print(f"📊 总样本数: {len(X_all)}, 特征数: {X_all.shape[1]}")
    
    return X_all, y_all


def train_deep_model(X_train, y_train, X_test, y_test, model_type='lstm', epochs=20, batch_size=256, seq_length=20):
    """训练深度学习模型"""
    
    device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
    print(f"🔧 使用设备: {device}")
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    X_train_seq, y_train_seq = create_sequences(X_train_scaled, y_train.values, seq_length)
    X_test_seq, y_test_seq = create_sequences(X_test_scaled, y_test.values, seq_length)
    
    X_train_tensor = torch.FloatTensor(X_train_seq).to(device)
    y_train_tensor = torch.FloatTensor(y_train_seq).to(device)
    X_test_tensor = torch.FloatTensor(X_test_seq).to(device)
    y_test_tensor = torch.FloatTensor(y_test_seq).to(device)
    
    train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    
    input_dim = X_train.shape[1]
    
    if model_type == 'lstm':
        model = LSTMModel(input_dim=input_dim, hidden_dim=64, num_layers=2, dropout=0.3)
    else:
        model = TransformerModel(input_dim=input_dim, d_model=64, nhead=4, num_layers=2, dropout=0.3)
    
    model = model.to(device)
    
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=3, factor=0.5)
    
    print(f"🚀 训练 {model_type.upper()} 模型...")
    
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        avg_loss = total_loss / len(train_loader)
        scheduler.step(avg_loss)
        
        if (epoch + 1) % 5 == 0:
            model.eval()
            with torch.no_grad():
                val_outputs = model(X_test_tensor)
                val_loss = criterion(val_outputs, y_test_tensor)
                val_pred = (val_outputs > 0.5).float()
                val_acc = (val_pred == y_test_tensor).float().mean()
                print(f"   Epoch {epoch+1}/{epochs}: Loss={avg_loss:.4f}, Val_Loss={val_loss:.4f}, Val_Acc={val_acc:.2%}")
    
    model.eval()
    with torch.no_grad():
        y_proba = model(X_test_tensor).cpu().numpy()
        y_pred = (y_proba > 0.5).astype(int)
        y_true = y_test_tensor.cpu().numpy()
    
    metrics = {
        'accuracy': accuracy_score(y_true, y_pred),
        'precision': precision_score(y_true, y_pred, zero_division=0),
        'recall': recall_score(y_true, y_pred, zero_division=0),
        'f1_score': f1_score(y_true, y_pred, zero_division=0),
        'auc': roc_auc_score(y_true, y_proba),
    }
    
    return model, metrics


def main():
    """主函数"""
    if not HAS_TORCH:
        print("❌ PyTorch 未安装，请运行: pip install torch")
        return
    
    print("=" * 60)
    print("      ML 准确率优化 v5 - 深度学习 (目标: 72% → 80%)")
    print("=" * 60)
    
    start_time = time.time()
    
    X, y = prepare_data(days=500, seq_length=20)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\n📊 训练集: {len(X_train)}, 测试集: {len(X_test)}")
    
    results = {}
    
    for model_type in ['lstm', 'transformer']:
        print(f"\n{'='*40}")
        print(f"  训练 {model_type.upper()} 模型")
        print('='*40)
        
        model, metrics = train_deep_model(
            X_train, y_train, X_test, y_test,
            model_type=model_type,
            epochs=30,
            batch_size=512,
            seq_length=20,
        )
        
        results[model_type] = metrics
        
        print(f"\n📈 {model_type.upper()} 模型结果:")
        print(f"   准确率:   {metrics['accuracy']:.2%}")
        print(f"   精确率:   {metrics['precision']:.2%}")
        print(f"   召回率:   {metrics['recall']:.2%}")
        print(f"   F1 分数:  {metrics['f1_score']:.2%}")
        print(f"   AUC:      {metrics['auc']:.4f}")
    
    total_time = time.time() - start_time
    print(f"\n⏱️ 总耗时: {total_time:.1f} 秒")
    
    best_model = max(results.keys(), key=lambda k: results[k]['accuracy'])
    best_acc = results[best_model]['accuracy']
    improvement = (best_acc - 0.72) / 0.72 * 100
    print(f"\n📈 最佳模型: {best_model.upper()}, 准确率: {best_acc:.2%}")
    print(f"   相比基准 72% {'↑' if improvement > 0 else '↓'}{abs(improvement):.1f}%")
    
    output_path = Path("models/optimization_v5_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'results': results,
            'best_model': best_model,
            'total_time': total_time,
        }, f, indent=2, default=str)
    print(f"📄 结果已保存: {output_path}")
    
    return results


if __name__ == "__main__":
    main()
