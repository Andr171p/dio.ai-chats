import {
  Check,
  ChevronDown,
  KeyRound,
  Monitor,
  Plug,
  Sparkle,
} from 'lucide-react';
import { useEffect } from 'react';
import { updateConversation, type Conversation } from '@/entities/conversation';
import {
  findModel,
  formatTokens,
  isSameModel,
  loadModels,
  setPreferredModel,
  useDefaultModel,
  useModels,
  type AvailableModel,
} from '@/entities/model';
import { navigate } from '@/shared/lib/navigation';
import { Badge } from '@/shared/ui/badge';
import { SOON_LABEL } from '@/shared/ui/button';
import { Menu, MenuItem, MenuLabel, MenuSeparator } from '@/shared/ui/menu';
import { usePopover } from '@/shared/ui/popover';
import { Spinner } from '@/shared/ui/spinner';
import styles from './ModelSelect.module.scss';

const soonBadge = <Badge>{SOON_LABEL}</Badge>;

/** Модель открытого чата или, для нового чата, модель по умолчанию. */
export function ModelSelect({ conversation }: { conversation?: Conversation }) {
  const { items, status, error } = useModels();
  const defaultModel = useDefaultModel();
  const selected = conversation
    ? findModel(items, conversation.model)
    : defaultModel;
  const menu = usePopover();

  useEffect(() => {
    void loadModels();
  }, []);

  const select = (model: AvailableModel) => {
    const selection = {
      connectionId: model.connectionId,
      modelId: model.modelId,
    };
    setPreferredModel(selection);

    if (conversation && !isSameModel(conversation.model, selection)) {
      // Ошибку откатит стор — модель в кнопке вернётся к прежней
      updateConversation(conversation.id, { model: selection }).catch(
        () => undefined,
      );
    }
  };

  return (
    <>
      <button type="button" className={styles.trigger} {...menu.triggerProps}>
        <Sparkle size={16} aria-hidden />
        <span className={styles.label}>
          {selected?.modelId ?? conversation?.model.modelId ?? 'Модель'}
        </span>
        <ChevronDown size={14} className={styles.chevron} aria-hidden />
      </button>

      <Menu
        {...menu.popoverProps}
        placement="top-end"
        className={styles.menu}
        aria-label="Выбор модели"
      >
        <div className={styles.heading}>
          <span className={styles.title}>Выберите модель</span>
          <span className={styles.subtitle}>
            Модель и место выполнения — ваш выбор.
          </span>
        </div>
        <MenuSeparator />

        <MenuItem
          icon={Sparkle}
          description="Подберёт модель под вашу задачу"
          disabled
          trailing={soonBadge}
        >
          DIOS Auto
        </MenuItem>

        <MenuLabel>DIOS</MenuLabel>
        {status === 'loading' && items.length === 0 && (
          <div className={styles.status}>
            <Spinner /> Загружаем модели…
          </div>
        )}
        {status === 'error' && <div className={styles.status}>{error}</div>}
        {status === 'ready' && items.length === 0 && (
          <div className={styles.status}>Нет доступных моделей</div>
        )}
        {items.map((model) => {
          const active = isSameModel(model, selected);
          return (
            <MenuItem
              key={`${model.connectionId}/${model.modelId}`}
              icon={Sparkle}
              selected={active}
              description={`${model.connectionName} · контекст ${formatTokens(model.contextWindow)}`}
              trailing={
                active && (
                  <Check size={16} className={styles.check} aria-hidden />
                )
              }
              onSelect={() => select(model)}
            >
              {model.modelId}
            </MenuItem>
          );
        })}

        <MenuLabel>Ваши модели</MenuLabel>
        <MenuItem
          icon={KeyRound}
          description="ChatGPT, Claude — запросы из вашего браузера"
          disabled
          trailing={soonBadge}
        >
          Личный аккаунт
        </MenuItem>
        <MenuItem
          icon={Monitor}
          description="Устройство в вашей сети"
          disabled
          trailing={soonBadge}
        >
          Локальная модель
        </MenuItem>

        <MenuSeparator />
        <MenuItem icon={Plug} onSelect={() => navigate({ page: 'models' })}>
          Управлять подключениями
        </MenuItem>
      </Menu>
    </>
  );
}
