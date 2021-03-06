import sklearn

from Classifier import Classifier


class AdaBoostClassifier(Classifier):
    def __init__(self, language='java', method_name='predict', class_name='Tmp'):
        super(self.__class__, self).__init__(language, method_name, class_name)
        if method_name not in ['predict']:
            msg = 'The classifier does not support the given method.'
            raise ValueError(msg)

    def port(self, model):
        if self.method_name == 'predict':
            return self.predict(model)

    def predict(self, model):
        class_name = self.class_name
        method_name = 'predict'

        # Check the used algorithm type:
        if model.algorithm not in ('SAMME.R'):
            msg = 'The classifier does not support the given algorithm %s.'
            raise ValueError(msg, model.algorithm)

        # Check type of base estimators:
        if not isinstance(model.base_estimator, sklearn.tree.tree.DecisionTreeClassifier):
            msg = 'The classifier does not support the given base estimator %s.'
            raise ValueError(msg, model.base_estimator)

        # Check number of base estimators:
        if not model.n_estimators > 0:
            msg = 'The classifier has not any base estimators.'
            raise ValueError(msg)

        # TODO: Use local variables
        # n_features = model.estimators_[0].n_features_
        # n_classes = model.n_classes_

        function_names = []
        functions = []
        n_estimators = 0
        for idx in range(model.n_estimators):
            weight = float(model.estimator_weights_[idx])
            if weight > 0:
                n_estimators += 1
                id = ("{0:0" + str(len(str(model.n_estimators))) + "d}").format(idx)
                function_name_with_id = method_name + "_" + id
                function_names.append(function_name_with_id)
                functions.append(AdaBoostClassifier._create_trees(
                    model.estimators_[idx], function_name_with_id))

        str_tree_calls = "\n".join(
            ['preds[{0}] = {1}.{2}(atts);'.format(int(i), class_name, function_name) for
             i, function_name in
             enumerate(function_names)])
        str_trees = '\n'.join(functions)
        str_method = AdaBoostClassifier._create_method(model, method_name, str_tree_calls,
                                                       n_estimators)
        str_class = AdaBoostClassifier._create_class(model, class_name, str_trees, str_method)
        return str_class

    @staticmethod
    def _create_trees(model, method_name):
        method_name = str(method_name)
        n_features = model.n_features_
        n_classes = model.n_classes_

        # @formatter:off
        def _recurse(left, right, threshold, value, features, node, depth):
            out = ''
            indent = '\n' + '    ' * depth
            if threshold[node] != -2.:
                out += indent + 'if (atts[{0}] <= {1:.16}f) {{'.format(features[node], threshold[node])
                if left[node] != -1.:
                    out += _recurse(left, right, threshold, value, features, left[node], depth + 1)
                out += indent + '} else {'
                if right[node] != -1.:
                    out += _recurse(left, right, threshold, value, features, right[node], depth + 1)
                out += indent + '}'
            else:
                out += ';'.join(
                    [indent + 'classes[{0}] = {1:.16}f'.format(i, v) for i, v in enumerate(value[node][0])]) + ';'
            return out
        # @formatter:on

        features = [[str(idx) for idx in range(n_features)][i] for i in model.tree_.feature]

        conditions = _recurse(
            model.tree_.children_left,
            model.tree_.children_right,
            model.tree_.threshold,
            model.tree_.value, features, 0, 1)

        # @formatter:off
        out = (
            'public static float[] {0}(float[] atts) {{ \n'
            '    int n_classes = {1}; \n'
            '    float[] classes = new float[n_classes]; \n'
            '    {2} \n\n'
            '    return classes; \n'
            '}}'
        ).format(method_name, n_classes, conditions)  # -> {0}, {1}, {2}
        # @formatter:on
        return str(out)

    @staticmethod
    def _create_method(model, method_name, str_trees, n_estimators):
        n_classes = model.n_classes_
        # @formatter:off
        out = (
            'public static int {0}(float[] atts) {{ \n'
            '    int n_estimators = {1}; \n'
            '    int n_classes = {2}; \n\n'
            '    float[][] preds = new float[n_estimators][]; \n'
            '    {3} \n\n'
            '    int i, j; \n'
            '    float normalizer, sum; \n'
            '    for (i = 0; i < n_estimators; i++) {{ \n'
            '        normalizer = 0.f; \n'
            '        for (j = 0; j < n_classes; j++) {{ \n'
            '            normalizer += preds[i][j]; \n'
            '        }} \n'
            '        if (normalizer == 0.f) {{ \n'
            '            normalizer = 1.0f; \n'
            '        }} \n'
            '        for (j = 0; j < n_classes; j++) {{ \n'
            '            preds[i][j] = preds[i][j] / normalizer; \n'
            '            if (preds[i][j] < 0.000000000000000222044604925f) {{ \n'
            '                preds[i][j] = 0.000000000000000222044604925f; \n'
            '            }} \n'
            '            preds[i][j] = (float) Math.log(preds[i][j]); \n'
            '        }} \n'
            '        sum = 0.0f; \n'
            '        for (j = 0; j < n_classes; j++) {{ \n'
            '            sum += preds[i][j]; \n'
            '        }} \n'
            '        for (j = 0; j < n_classes; j++) {{ \n'
            '            preds[i][j] = (n_classes - 1) * (preds[i][j] - (1.f / n_classes) * sum); \n'
            '        }} \n'
            '    }} \n'
            '    float[] classes = new float[n_classes]; \n'
            '    for (i = 0; i < n_estimators; i++) {{ \n'
            '        for (j = 0; j < n_classes; j++) {{ \n'
            '            classes[j] += preds[i][j]; \n'
            '        }} \n'
            '    }} \n'
            '    int idx = 0; \n'
            '    float val = Float.NEGATIVE_INFINITY; \n'
            '    for (i = 0; i < n_classes; i++) {{ \n'
            '        if (classes[i] > val) {{ \n'
            '            idx = i; \n'
            '            val = classes[i]; \n'
            '        }} \n'
            '    }} \n'
            '    return idx; \n'
            '}}').format(method_name, n_estimators, n_classes, str_trees)
        # @formatter:on
        return str(out)

    @staticmethod
    def _create_class(model, class_name, str_trees, str_method):
        n_features = model.estimators_[0].n_features_
        # @formatter:off
        out = (
            'class {0} {{ \n'
            '    {1} \n'
            '    {2} \n'
            '    public static void main(String[] args) {{ \n'
            '        if (args.length == {3}) {{ \n'
            '            float[] atts = new float[args.length]; \n'
            '            for (int i = 0; i < args.length; i++) {{ \n'
            '                atts[i] = Float.parseFloat(args[i]); \n'
            '            }} \n'
            '            System.out.println({0}.predict(atts)); \n'
            '        }} \n'
            '    }} \n'
            '}}').format(class_name, str_trees, str_method, n_features)
        # @formatter:on
        return str(out)
