import {getTraceContext} from 'sentry/components/events/interfaces/spans/utils';
import {IconWarning} from 'sentry/icons';
import {t} from 'sentry/locale';
import {Event} from 'sentry/types/event';
import EmptyMessage from 'sentry/views/settings/components/emptyMessage';

import SpanTree from './spanTree';
import {isTransactionEvent} from './utils';

type Props = {
  baselineEvent: Event;
  regressionEvent: Event;
};

const TraceView = (props: Props) => {
  const {baselineEvent, regressionEvent} = props;

  if (!isTransactionEvent(baselineEvent) || !isTransactionEvent(regressionEvent)) {
    return (
      <EmptyMessage>
        <IconWarning color="gray300" size="lg" />
        <p>{t('One of the given events is not a transaction.')}</p>
      </EmptyMessage>
    );
  }

  const baselineTraceContext = getTraceContext(baselineEvent);
  const regressionTraceContext = getTraceContext(regressionEvent);

  if (!baselineTraceContext || !regressionTraceContext) {
    return (
      <EmptyMessage>
        <IconWarning color="gray300" size="lg" />
        <p>{t('There is no trace found in either of the given transactions.')}</p>
      </EmptyMessage>
    );
  }

  return <SpanTree baselineEvent={baselineEvent} regressionEvent={regressionEvent} />;
};

export default TraceView;
